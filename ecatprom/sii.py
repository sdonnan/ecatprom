from promtypes import *
from io import BytesIO
import enum  # we keep the namespace to avoid collisions with our prom enum


def from_file(fname):
    f = open(fname, 'rb')
    d = Sii()
    d.take(Reader(f))
    return d


class CatType(enum.IntEnum):
    '''Enumerated values for specific categories

    We use the names verbatim from the spec, so the capitalization is wonky
    '''
    NOP = 0
    STRINGS = 10
    General = 30
    FMMU = 40
    SyncM = 41
    FMMUX = 42
    SyncUnit = 43
    TXPDO = 50
    RXPDO = 51
    DC = 60
    END = 0xFFFF

# you know what? this is probably what metaclasses are for


def MbxCfg(): return Struct(
    recv_mbx_offset=Int(16),
    recv_mbx_size=Int(16),
    send_mbx_offset=Int(16),
    send_mbx_size=Int(16),
)


def InfoStructure(): return Struct(
    pdi_control=Int(16),
    pdi_config=Int(16),
    sync_impulse_len=Int(16),
    pdi_config_2=Int(16),
    configured_alias=Int(16),
    reserved1=NullBytes(4),
    checksum=Int(16),
    id=Struct(
        vendor_id=Int(32),
        product_code=Int(32),
        revision_number=Int(32),
        serial_number=Int(32),
    ),
    reserved2=NullBytes(8),
    bootstrap_mbx=MbxCfg(),
    standard_mbx=MbxCfg(),
    mbx_protocol=Struct(
        AoE=Int(1),
        EoE=Int(1),
        CoE=Int(1),
        FoE=Int(1),
        SoE=Int(1),
        VoE=Int(1),
        reserved=NullBits(10),
    ),
    reserved3=NullBytes(66),
    size=Int(16),
    version=Int(16),
)


def DescriptionOfPort(): return Enum(
    bits=4,
    options={
        0x00: "UNUSED",
        0x01: "MII",
        0x02: "RESERVED",
        0x03: "EBUS",
        0x04: "FAST HOT CONNECT",
    }
)


def CategoryGeneral(): return Struct(
    group_idx=Int(8),
    img_idx=Int(8),
    order_idx=Int(8),
    name_idx=Int(8),
    reserved=Int(8),
    coe_details=Struct(
        enable_sdo=Int(1),
        enable_sdo_info=Int(1),
        enable_pdo_assign=Int(1),
        enable_pdo_config=Int(1),
        enable_upload_at_start=Int(1),
        enable_complete_sdo_access=Int(1),
        reserved=NullBits(2),
    ),
    foe_details=Struct(
        enable_foe=Int(1),
        reserved=NullBits(7),
    ),
    eoe_details=Struct(
        enable_eoe=Int(1),
        reserved=NullBits(7),
    ),
    soe_channels=NullBytes(1),
    ds402_channels=NullBytes(1),
    sysman_class=NullBytes(1),
    flags=Struct(
        enable_safe_op=Int(1),
        enable_not_lrw=Int(1),
        mbox_data_link_layer=Int(1),
        ident_als_ts=Int(1),
        ident_phy_m=Int(1),
        reserved=NullBits(3),
    ),
    current_on_ebus=Int(16),
    group_idx_1=Int(8),
    reserved1=NullBytes(1),
    physical_port=Struct(
        port0=DescriptionOfPort(),
        port1=DescriptionOfPort(),
        port2=DescriptionOfPort(),
        port3=DescriptionOfPort(),
    ),
    physical_memory_address=Int(16),
    reserved2=NullBytes(12),
)


def Fmmu(): return Enum(
    bits=8,
    options={
        0x00: "UNUSED",
        0x01: "OUTPUTS",
        0x02: "INPUTS",
        0x03: "SYNCM STATUS",
        0xFF: "UNUSED",
    }
)


def FmmuEx(): return Struct(
    op_only=Int(1),
    sm_defined=Int(1),
    su_defined=Int(1),
    reserved=NullBits(5),
    sm=Int(8),
    su=Int(8),
)


def SyncM(): return Struct(
    physical_start_addr=Int(16),
    length=Int(16),
    control_register=Int(8),  # TODO expand
    status_register=NullBytes(1),
    enable_sync_mananger=Struct(
        enable=Int(1),
        fixed_content=Int(1),
        virtual_sync_manager=Int(1),
        op_only=Int(1),
        reserved=NullBits(4),
    ),
    sync_manager_type=Enum(
        bits=8,
        options={
            0x00: "UNUSED",
            0x01: "MBX_OUT",
            0x02: "MBX_IN",
            0x03: "PROCESS_DATA_OUT",
            0x04: "PROCESS_DATA_IN",
        }
    )
)


def CategoryHeader(): return Struct(
    category_type=Int(16),
    len_in_words=Int(16),
)


def CategoryDc(): return Struct(
    cycle_time_0=Int(32),
    shift_time_0=Int(32),
    shift_time_1=Int(32),
    sync1_cycle_factor=Int(16),
    assign_activate=Int(16),
    sync0_cycle_factor=Int(16),
    name_idx=Int(8),
    desc_idx=Int(8),
    reserved=NullBytes(4),
)


class Sii:

    def __init__(self):
        self.info = None
        self.strings = None
        self.general = None
        self.fmmu = None
        self.syncm = None
        self.fmmux = None
        self.sync_unit = None
        self.txpdo = None
        self.rxpdo = None
        self.dc = None
        # we track these so we can reserialize as is
        self.unknown = []  # (category type, bytes)

    def take(self, reader):
        self.info = InfoStructure()
        self.info.take(reader)
        self.take_categories(reader)

    def take_categories(self, reader):
        header = CategoryHeader()
        while True:
            # read the header
            header.take(reader)
            cat_id = header.category_type.value
            nbytes = header.len_in_words.value * 2
            # exit the loop if we are done
            if cat_id == CatType.END:
                break
            # move the data into a separate buffer so misbehaving defintions can be detected
            buffer = BytesIO(reader.read_bytes(nbytes))
            # elif header.cat_type == CatType.STRINGS:
            if cat_id == CatType.General:
                self.general = CategoryGeneral()
                self.general.take(Reader(buffer))
                if buffer.read():
                    raise RuntimeError(
                        'Data for General Category is malformed')
            elif cat_id == CatType.DC:
                self.dc = CategoryDc()
                self.dc.take(Reader(buffer))
                if buffer.read():
                    raise RuntimeError('Data for DC Category is malformed')
            elif cat_id == CatType.STRINGS:
                # get the length of the string section
                r = Reader(buffer)
                l = Int(8)
                l.take(r)
                # and read them
                self.strings = Array(item_type=String, count=l.value)
                self.strings.take(r)
                if len(buffer.read()) > 1:  # padding may be added
                    raise RuntimeError('Data for String Category is malformed')
            elif cat_id == CatType.FMMU:
                self.fmmu = Array(item_type=Fmmu)
                self.fmmu.take(Reader(buffer))
                if len(buffer.read()) > 1:  # padding may be added
                    raise RuntimeError('Data for FMMU Category is malformed')
            elif cat_id == CatType.FMMUX:
                self.fmmux = Array(item_type=FmmuEx)
                self.fmmux.take(Reader(buffer))
                if len(buffer.read()) > 1:  # padding may be added
                    raise RuntimeError(
                        'Data for FMMU EX Category is malformed')
            elif cat_id == CatType.SyncM:
                self.syncm = Array(item_type=SyncM)
                self.syncm.take(Reader(buffer))
                if len(buffer.read()) > 1:  # padding may be added
                    raise RuntimeError('Data for SyncM Category is malformed')
            else:
                self.unknown.append((cat_id, buffer.read()))

    def __str__(self):
        lines = []
        for member in self.__dict__.keys():
            m = getattr(self, member)
            if isinstance(m, Item):
                lines.append('== {} =='.format(member.upper()))
                lines.append(str(m))
        if self.unknown:
            lines.append("== UKNOWN ==")
            for cat_id, data in self.unknown:
                lines.append(
                    "Category 0x{:04X}. {} Bytes".format(cat_id, len(data)))
        return '\n'.join(lines)
