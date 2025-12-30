import re
import sys
from pathlib import Path
from typing import Any

from datamodel_code_generator.__main__ import main as codegen_main
from pydantic import BaseModel


def _patched_deepcopy(self: BaseModel, memo: dict[int, Any] | None = None) -> BaseModel:
    """Avoid fully-recursive deepcopy to prevent excessive memory usage."""

    # Reuse BaseModel.copy to produce a shallow copy. This is sufficient for
    # datamodel-code-generator, which only needs independent instances of the
    # models without recursively cloning every nested object.
    clone = self.copy(deep=False)
    if memo is None:
        memo = {}
    memo[id(self)] = clone
    return clone


def _extract_output_path(args: list[str]) -> Path | None:
    """Extract the `--output` path from datamodel-code-generator CLI args."""

    if "--output" in args:
        index = args.index("--output")
        try:
            return Path(args[index + 1]).resolve()
        except IndexError:
            return None

    pattern = re.compile(r"^--output=(?P<value>.+)$")
    for arg in args:
        match = pattern.match(arg)
        if match:
            return Path(match.group("value")).resolve()

    return None


def _patch_transfer_picker_schema(output_path: Path) -> None:
    """Tighten TransferPickerControlSchema typing post generation."""

    try:
        content = output_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return

    replacement = (
        "class TransferPickerControlSchema(BaseTransferControlSchema, SpinnerExtraProps):\n"
        "    type: Literal['transfer-picker'] = Field(\n"
        "        ..., description='TransferPicker 穿梭器的弹框形态 文档：https://aisuda.bce.baidu.com/amis/zh-CN/components/form/transfer-picker'\n"
        "    )\n"
        "    borderMode: BorderMode | None = Field(None, description='边框模式，全边框，还是半边框，或者没边框。')\n"
        "    pickerSize: Size | None = Field(None, description='弹窗大小')\n"
    )

    pattern = re.compile(
        r"class TransferPickerControlSchema\(BaseModel\):\n(?:    .+\n)+?    pickerSize: Any \| None = None\n",
        re.MULTILINE,
    )

    new_content, count = pattern.subn(replacement, content)
    if count:
        output_path.write_text(new_content, encoding="utf-8")

def main() -> None:
    # datamodel-code-generator builds deeply nested pydantic models. Increase
    # recursion limit so deepcopy() inside the library can finish without
    # hitting the default recursion depth (1000) on large schemas.
    sys.setrecursionlimit(10000)

    # Monkey-patch BaseModel.__deepcopy__ once before invoking the generator.
    BaseModel.__deepcopy__ = _patched_deepcopy  # type: ignore[assignment[attr-defined]]

    args = sys.argv[1:]
    codegen_main(args)

    output_path = _extract_output_path(args)
    if output_path is not None:
        _patch_transfer_picker_schema(output_path)


if __name__ == "__main__":
    main()
