#!/usr/bin/env python3
#
# Cross Platform and Multi Architecture Advanced Binary Emulation Framework
#

from functools import cached_property
from typing import Optional

from unicorn import Uc, UC_ARCH_MIPS, UC_MODE_MIPS32, UC_MODE_BIG_ENDIAN, UC_MODE_LITTLE_ENDIAN
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_BIG_ENDIAN, CS_MODE_LITTLE_ENDIAN
from keystone import Ks, KS_ARCH_MIPS, KS_MODE_MIPS32, KS_MODE_BIG_ENDIAN, KS_MODE_LITTLE_ENDIAN

from qiling import Qiling
from qiling.arch.arch import QlArch
from qiling.arch import mips_const
from qiling.arch.models import MIPS_CPU_MODEL
from qiling.arch.register import QlRegisterManager
from qiling.const import QL_ARCH, QL_ENDIAN


class QlArchMIPS(QlArch):
    type = QL_ARCH.MIPS
    bits = 32

    def __init__(self, ql: Qiling, *, cputype: Optional[MIPS_CPU_MODEL], endian: QL_ENDIAN):
        super().__init__(ql, cputype=cputype)

        self._init_endian = endian

    @cached_property
    def uc(self) -> Uc:
        endian = {
            QL_ENDIAN.EB: UC_MODE_BIG_ENDIAN,
            QL_ENDIAN.EL: UC_MODE_LITTLE_ENDIAN
        }[self.endian]

        return Uc(UC_ARCH_MIPS, UC_MODE_MIPS32 + endian)

    @cached_property
    def regs(self) -> QlRegisterManager:
        regs_map = dict(
            **mips_const.reg_map
        )

        pc_reg = 'pc'
        sp_reg = 'sp'

        return QlRegisterManager(self.uc, regs_map, pc_reg, sp_reg)

    @cached_property
    def disassembler(self) -> Cs:
        endian = {
            QL_ENDIAN.EL: CS_MODE_LITTLE_ENDIAN,
            QL_ENDIAN.EB: CS_MODE_BIG_ENDIAN
        }[self.endian]

        return Cs(CS_ARCH_MIPS, CS_MODE_MIPS32 + endian)

    @cached_property
    def assembler(self) -> Ks:
        endian = {
            QL_ENDIAN.EL: KS_MODE_LITTLE_ENDIAN,
            QL_ENDIAN.EB: KS_MODE_BIG_ENDIAN
        }[self.endian]

        return Ks(KS_ARCH_MIPS, KS_MODE_MIPS32 + endian)

    @property
    def endian(self) -> QL_ENDIAN:
        return self._init_endian
