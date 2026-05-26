from typing import Dict, List, Optional, Set

from miniparser.ast_nodes import (
    Visitor, ASTNode, Program,
    FnDecl, VarDecl, StructDecl, Param, StructField,
    BlockStmt, IfStmt, WhileStmt, ForStmt, ReturnStmt, ExprStmt,
    BinaryExpr, UnaryExpr, AssignExpr, CallExpr,
    IdentifierExpr, IntLiteral, FloatLiteral, StringLiteral, BoolLiteral,
)
from .instructions import BasicBlock, IRFunction, IRProgram, Instruction, Opcode

# таблица: бинарный оператор AST -> опкод IR
_BINARY_OPS: Dict[str, Opcode] = {
    "+":  Opcode.ADD,    "-":  Opcode.SUB,
    "*":  Opcode.MUL,    "/":  Opcode.DIV,    "%":  Opcode.MOD,
    "==": Opcode.CMP_EQ, "!=": Opcode.CMP_NE,
    "<":  Opcode.CMP_LT, "<=": Opcode.CMP_LE,
    ">":  Opcode.CMP_GT, ">=": Opcode.CMP_GE,
    "&&": Opcode.AND,    "||": Opcode.OR,
}

# таблица: составной оператор присваивания -> опкод IR
_COMPOUND_OPS: Dict[str, Opcode] = {
    "+=": Opcode.ADD, "-=": Opcode.SUB,
    "*=": Opcode.MUL, "/=": Opcode.DIV,
}


class IRGenerator(Visitor):
    def __init__(self):
        self._program = IRProgram()
        self._current_fn: Optional[IRFunction] = None
        self._current_block: Optional[BasicBlock] = None
        # состояние, сбрасываемое для каждой функции
        self._temp_count = 0
        self._var_slot_counter: Dict[str, int] = {}
        self._var_map: Dict[str, str] = {}           # имя -> слот (напр. "x_0")
        self._scope_stack: List[Dict[str, Optional[str]]] = []
        # глобальный счётчик меток, чтобы метки были уникальны в программе
        self._label_count = 0

    # ── Публичный интерфейс ───────────────────────────────────────────────────

    def generate(self, ast: Program) -> IRProgram:
        ast.accept(self)
        for fn in self._program.functions:
            self._resolve_edges(fn)
        return self._program

    def get_program(self) -> IRProgram:
        return self._program

    # ── Вспомогательные методы ────────────────────────────────────────────────

    def _new_temp(self) -> str:
        t = f"t{self._temp_count}"
        self._temp_count += 1
        return t

    def _new_label(self, hint: str = "L") -> str:
        lbl = f"{hint}_{self._label_count}"
        self._label_count += 1
        return lbl

    def _new_block(self, label: str) -> BasicBlock:
        block = BasicBlock(label)
        if self._current_fn is not None:
            self._current_fn.blocks.append(block)
        return block

    def _set_block(self, block: BasicBlock):
        self._current_block = block

    def _emit(self, instr: Instruction):
        if self._current_block is not None:
            self._current_block.instructions.append(instr)

    def _block_terminated(self) -> bool:
        if not self._current_block or not self._current_block.instructions:
            return False
        last_op = self._current_block.instructions[-1].opcode
        return last_op in {Opcode.JUMP, Opcode.JUMP_IF, Opcode.JUMP_IF_NOT, Opcode.RETURN}

    def _push_scope(self):
        self._scope_stack.append({})

    def _pop_scope(self):
        if not self._scope_stack:
            return
        saved = self._scope_stack.pop()
        for name, old_slot in saved.items():
            if old_slot is None:
                self._var_map.pop(name, None)
            else:
                self._var_map[name] = old_slot

    def _declare_var(self, name: str) -> str:
        """Выделяем новый именованный слот для переменной и регистрируем в области видимости."""
        idx = self._var_slot_counter.get(name, 0)
        self._var_slot_counter[name] = idx + 1
        slot = f"{name}_{idx}"
        if self._scope_stack:
            # сохраняем предыдущий слот, чтобы восстановить при выходе из области
            if name not in self._scope_stack[-1]:
                self._scope_stack[-1][name] = self._var_map.get(name)
        self._var_map[name] = slot
        return slot

    def _gen_expr(self, node: ASTNode) -> str:
        """Генерируем выражение; возвращаем имя временной переменной или литерал."""
        result = node.accept(self)
        return str(result) if result is not None else "0"

    def _resolve_edges(self, fn: IRFunction):
        """Восстанавливаем рёбра CFG по меткам переходов."""
        label_to_block = {b.label: b for b in fn.blocks}
        for block in fn.blocks:
            for instr in block.instructions:
                if instr.opcode in {Opcode.JUMP, Opcode.JUMP_IF, Opcode.JUMP_IF_NOT}:
                    target_label = instr.args[-1]
                    target = label_to_block.get(target_label)
                    if target and target not in block.successors:
                        block.successors.append(target)
                        target.predecessors.append(block)

    # ── Программа ─────────────────────────────────────────────────────────────

    def visit_program(self, node: Program):
        for decl in node.declarations:
            decl.accept(self)

    # ── Объявления ────────────────────────────────────────────────────────────

    def visit_fn_decl(self, node: FnDecl):
        params = [(p.name, p.type_name) for p in node.params]
        fn = IRFunction(node.name, node.return_type or "void", params)
        self._program.functions.append(fn)
        self._current_fn = fn

        # сбрасываем состояние для новой функции
        self._temp_count = 0
        self._var_slot_counter = {}
        self._var_map = {}
        self._scope_stack = []

        entry = self._new_block("entry")
        self._set_block(entry)

        # область видимости функции: параметры как локальные слоты
        self._push_scope()
        for p in node.params:
            slot = self._declare_var(p.name)
            # значение параметра копируется в локальный слот при вызове
            self._emit(Instruction(Opcode.PARAM, slot, [p.name], f"{p.type_name} {p.name}"))

        node.body.accept(self)
        self._pop_scope()

        # если тело не заканчивается явным возвратом — добавляем неявный
        if not self._block_terminated():
            self._emit(Instruction(Opcode.RETURN, None, [], "неявный возврат"))

    def visit_var_decl(self, node: VarDecl):
        slot = self._declare_var(node.name)
        if node.initializer is not None:
            t = self._gen_expr(node.initializer)
            self._emit(Instruction(
                Opcode.STORE, None, [f"[{slot}]", t],
                f"{node.type_name} {node.name}",
            ))

    def visit_struct_decl(self, node: StructDecl):
        pass  # объявление типа не генерирует код

    def visit_param(self, node: Param):
        pass  # параметры обрабатываются в visit_fn_decl

    def visit_struct_field(self, node: StructField):
        pass

    # ── Операторы ─────────────────────────────────────────────────────────────

    def visit_block_stmt(self, node: BlockStmt):
        self._push_scope()
        for stmt in node.body:
            stmt.accept(self)
        self._pop_scope()

    def visit_if_stmt(self, node: IfStmt):
        t_cond = self._gen_expr(node.condition)

        l_then  = self._new_label("L_then")
        l_else  = self._new_label("L_else") if node.else_branch else None
        l_endif = self._new_label("L_endif")

        self._emit(Instruction(Opcode.JUMP_IF, None, [t_cond, l_then]))
        self._emit(Instruction(Opcode.JUMP,    None, [l_else or l_endif]))

        # блок then
        b_then = self._new_block(l_then)
        self._set_block(b_then)
        node.then_branch.accept(self)
        if not self._block_terminated():
            self._emit(Instruction(Opcode.JUMP, None, [l_endif]))

        # блок else (если есть)
        if node.else_branch:
            b_else = self._new_block(l_else)
            self._set_block(b_else)
            node.else_branch.accept(self)
            if not self._block_terminated():
                self._emit(Instruction(Opcode.JUMP, None, [l_endif]))

        # блок объединения после if
        b_endif = self._new_block(l_endif)
        self._set_block(b_endif)

    def visit_while_stmt(self, node: WhileStmt):
        l_header = self._new_label("L_while")
        l_body   = self._new_label("L_while_body")
        l_after  = self._new_label("L_while_after")

        # безусловный переход к заголовку цикла
        self._emit(Instruction(Opcode.JUMP, None, [l_header]))

        # заголовок: проверка условия
        b_header = self._new_block(l_header)
        self._set_block(b_header)
        t_cond = self._gen_expr(node.condition)
        self._emit(Instruction(Opcode.JUMP_IF, None, [t_cond, l_body]))
        self._emit(Instruction(Opcode.JUMP,    None, [l_after]))

        # тело цикла
        b_body = self._new_block(l_body)
        self._set_block(b_body)
        node.body.accept(self)
        if not self._block_terminated():
            self._emit(Instruction(Opcode.JUMP, None, [l_header]))

        # блок после цикла
        b_after = self._new_block(l_after)
        self._set_block(b_after)

    def visit_for_stmt(self, node: ForStmt):
        # отдельная область для init-переменной (напр. for (int i = 0; ...))
        self._push_scope()

        if node.init is not None:
            node.init.accept(self)

        l_header = self._new_label("L_for")
        l_body   = self._new_label("L_for_body")
        l_after  = self._new_label("L_for_after")

        self._emit(Instruction(Opcode.JUMP, None, [l_header]))

        # заголовок: проверка условия
        b_header = self._new_block(l_header)
        self._set_block(b_header)
        if node.condition is not None:
            t_cond = self._gen_expr(node.condition)
            self._emit(Instruction(Opcode.JUMP_IF, None, [t_cond, l_body]))
            self._emit(Instruction(Opcode.JUMP,    None, [l_after]))
        else:
            self._emit(Instruction(Opcode.JUMP, None, [l_body]))

        # тело цикла + обновление
        b_body = self._new_block(l_body)
        self._set_block(b_body)
        node.body.accept(self)
        if node.update is not None:
            self._gen_expr(node.update)
        if not self._block_terminated():
            self._emit(Instruction(Opcode.JUMP, None, [l_header]))

        # блок после цикла
        b_after = self._new_block(l_after)
        self._set_block(b_after)

        self._pop_scope()

    def visit_return_stmt(self, node: ReturnStmt):
        if node.value is not None:
            t = self._gen_expr(node.value)
            self._emit(Instruction(Opcode.RETURN, None, [t]))
        else:
            self._emit(Instruction(Opcode.RETURN, None, []))

    def visit_expr_stmt(self, node: ExprStmt):
        self._gen_expr(node.expr)

    # ── Выражения (возвращают имя временной переменной или строку литерала) ───

    def visit_binary_expr(self, node: BinaryExpr) -> str:
        t1 = self._gen_expr(node.left)
        t2 = self._gen_expr(node.right)
        t  = self._new_temp()
        self._emit(Instruction(_BINARY_OPS[node.op], t, [t1, t2]))
        return t

    def visit_unary_expr(self, node: UnaryExpr) -> str:
        t_op = self._gen_expr(node.operand)
        t    = self._new_temp()
        op   = Opcode.NEG if node.op == "-" else Opcode.NOT
        self._emit(Instruction(op, t, [t_op]))
        return t

    def visit_assign_expr(self, node: AssignExpr) -> str:
        t_val = self._gen_expr(node.value)
        slot  = self._var_map.get(node.target, node.target)

        if node.op == "=":
            self._emit(Instruction(Opcode.STORE, None, [f"[{slot}]", t_val], node.target))
        else:
            # составное присваивание: загружаем, применяем операцию, сохраняем
            t_cur = self._new_temp()
            self._emit(Instruction(Opcode.LOAD, t_cur, [f"[{slot}]"]))
            t_res = self._new_temp()
            self._emit(Instruction(_COMPOUND_OPS[node.op], t_res, [t_cur, t_val]))
            self._emit(Instruction(Opcode.STORE, None, [f"[{slot}]", t_res]))

        return t_val

    def visit_call_expr(self, node: CallExpr) -> str:
        arg_temps = [self._gen_expr(a) for a in node.args]
        t = self._new_temp()
        self._emit(Instruction(Opcode.CALL, t, [node.callee] + arg_temps))
        return t

    def visit_identifier_expr(self, node: IdentifierExpr) -> str:
        slot = self._var_map.get(node.name, node.name)
        t    = self._new_temp()
        self._emit(Instruction(Opcode.LOAD, t, [f"[{slot}]"], node.name))
        return t

    def visit_int_literal(self, node: IntLiteral) -> str:
        return str(node.value)

    def visit_float_literal(self, node: FloatLiteral) -> str:
        return str(node.value)

    def visit_bool_literal(self, node: BoolLiteral) -> str:
        return "1" if node.value else "0"

    def visit_string_literal(self, node: StringLiteral) -> str:
        return repr(node.value)
