from typing import List
from .instructions import BasicBlock, IRFunction, IRProgram, Opcode


class IRTextPrinter:
    """Выводит IR в текстовом виде: одна инструкция на строку."""

    def render(self, program: IRProgram) -> str:
        return "\n\n".join(self._render_fn(fn) for fn in program.functions)

    def _render_fn(self, fn: IRFunction) -> str:
        params_str = ", ".join(f"{t} {n}" for n, t in fn.params)
        lines: List[str] = [f"function {fn.name}: {fn.return_type} ({params_str})"]
        for block in fn.blocks:
            lines.append(f"  {block.label}:")
            for instr in block.instructions:
                lines.append(f"    {instr}")
        return "\n".join(lines)


class IRDotPrinter:
    """Выводит граф потока управления (CFG) в формате Graphviz DOT."""

    def render(self, program: IRProgram) -> str:
        lines = [
            "digraph CFG {",
            '  node [shape=record fontname="monospace" style=filled fillcolor=lightyellow];',
        ]
        for fn in program.functions:
            lines.append(f'  subgraph cluster_{fn.name} {{')
            lines.append(f'    label="{fn.name}";')
            lines.append('    style=rounded;')
            for block in fn.blocks:
                lbl = self._block_label(block)
                nid = f"{fn.name}__{block.label}"
                lines.append(f'    {nid} [label="{lbl}"];')
            for block in fn.blocks:
                src_id = f"{fn.name}__{block.label}"
                for succ in block.successors:
                    dst_id = f"{fn.name}__{succ.label}"
                    lines.append(f'    {src_id} -> {dst_id};')
            lines.append("  }")
        lines.append("}")
        return "\n".join(lines)

    def _block_label(self, block: BasicBlock) -> str:
        instrs = "\\l".join(str(i) for i in block.instructions)
        header = f"{block.label}:"
        body   = instrs + "\\l" if instrs else ""
        raw    = f"{header}\\l{body}"
        return raw.replace('"', '\\"').replace("[", "\\[").replace("]", "\\]")
