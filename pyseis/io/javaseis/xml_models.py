from pathlib import Path
import xml.etree.ElementTree as ET
from typing import Optional, Type, TypeVar, Dict, Any, List, Union
from enum import Enum
from dataclasses import dataclass, field, fields
import numpy as np

T = TypeVar('T', bound='XMLDataclass')

class Policy(str, Enum):
    RANDOM = "RANDOM"
    SEQUENTIAL = "SEQUENTIAL"

@dataclass(order=True)
class XMLDataclass:
    """Base class for XML-serializable dataclasses"""
    
    @staticmethod
    def get_type(value: str, field_type: Type) -> Any:
        """Convert string value to appropriate type based on field type annotation"""
        value = value.strip()
        
        # Handle Optional types
        if hasattr(field_type, '__origin__') and field_type.__origin__ is Union:
            # Get the non-None type from Optional
            actual_type = next(t for t in field_type.__args__ if t is not type(None))
            return XMLDataclass.get_type(value, actual_type)
        
        # Handle List types
        if hasattr(field_type, '__origin__') and field_type.__origin__ is list:
            element_type = field_type.__args__[0]
            values = [v.strip() for v in value.split('\n') if v.strip()]
            return [element_type(v.strip('"')) for v in values]
        
        # Handle single values
        if field_type == bool:
            return value.lower() == 'true'
        elif field_type in (np.int32, int):
            return np.int32(int(value))
        elif field_type == np.int64:
            return np.int64(int(value))
        elif field_type == np.float32:
            return np.float32(float(value))
        elif field_type == np.float64:
            return np.float64(float(value))
        elif field_type == str:
            return value.strip('"')
        else:
            return field_type(value)

    @staticmethod
    def set_type(value: Any, field_type: Type) -> tuple[str, str]:
        """Convert value to string and determine its type string
        
        Args:
            value: Value to convert
            field_type: Type annotation from dataclass field
            
        Returns:
            Tuple of (type_str, value_str)
        """
        # Handle List types
        if field_type.__origin__ is list:
            element_type = field_type.__args__[0]
            if element_type == str:
                return 'string', XMLDataclass.PAD + XMLDataclass.PAD.join(str(x) for x in value) + XMLDataclass.PAD_END
            elif element_type == np.int32:
                return 'int', XMLDataclass.PAD + XMLDataclass.PAD.join(str(int(x)) for x in value) + XMLDataclass.PAD_END
            elif element_type == np.int64:
                return 'long', XMLDataclass.PAD + XMLDataclass.PAD.join(str(int(x)) for x in value) + XMLDataclass.PAD_END
            elif element_type == np.float32:
                return 'float', XMLDataclass.PAD + XMLDataclass.PAD.join(str(float(x)) for x in value) + XMLDataclass.PAD_END
            elif element_type == np.float64:
                return 'double', XMLDataclass.PAD + XMLDataclass.PAD.join(str(float(x)) for x in value) + XMLDataclass.PAD_END
        
        # Handle single values
        if isinstance(value, bool):
            return 'boolean', str(value).lower()
        elif isinstance(value, np.int32):
            return 'int', str(int(value))
        elif isinstance(value, np.int64):
            return 'long', str(int(value))
        elif isinstance(value, np.float32):
            return 'float', str(float(value))
        elif isinstance(value, np.float64):
            return 'double', str(float(value))
        elif isinstance(value, str):
            return 'string', f'"{value}"'
        else:
            return 'string', str(value)

    def from_xml(self, xml_path: Optional[Path] = None) -> None:
        """Read instance from XML file"""
        if xml_path is None:
            xml_path = Path(self.filename)
            
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # Find parset anywhere in the tree
        parset = root if (root.tag == 'parset' and root.get('name') == self.root_name) else root.find(f".//parset[@name='{self.root_name}']")
        
        if parset is None:
            raise ValueError(f"Could not find parset with name {self.root_name}")
        
        # Update values from XML
        for field in fields(self.__class__):
            if field.name in ['filename', 'root_name', 'parent']:
                continue
                
            par = parset.find(f"./par[@name='{field.name}']")
            if par is not None:
                value = par.text if par.text else ""
                field_type = field.type
                parsed_value = self.get_type(value, field_type)
                setattr(self, field.name, parsed_value)

    def to_xml(self, xml_path: Optional[Path] = None) -> ET.Element:
        """Create new XML file from this instance
        
        Args:
            xml_path: Optional override for the default filename
            
        Returns:
            The created XML element
        """
        # Use provided path or default filename
        if xml_path is None:
            xml_path = Path(self.filename)
            
        # Create root element with proper nesting
        if self.parent:
            root = ET.Element('parset', name=self.parent)
            element = ET.SubElement(root, 'parset', name=self.root_name)
        else:
            root = ET.Element('parset', name=self.root_name)
            element = root
        
        # Get field types and maintain order from dataclass
        class_fields = fields(self)
        
        for field in class_fields:
            # Skip metadata fields
            if field.name in ['filename', 'root_name', 'parent']:
                continue
                
            name = field.name
            value = getattr(self, name)
            
            # Handle nested dataclasses
            if isinstance(value, XMLDataclass):
                nested = value.to_xml()
                element.append(nested)
                continue
            
            # Handle regular fields
            type_str, value_str = self.set_type(value, field.type)
            par = ET.SubElement(element, 'par', name=name)
            par.text = value_str
            par.set('type', type_str)
                
        tree = ET.ElementTree(root)
        tree.write(xml_path, encoding='utf-8', xml_declaration=True)
        
        return element

    def update_xml(self, xml_path: Optional[Path] = None) -> None:
        """Update existing XML file with values from this instance
        
        Args:
            xml_path: Optional override for the default filename
        """
        if xml_path is None:
            xml_path = Path(self.filename)
            
        # Read existing file
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # Find our parset
        parset = root.find(f".//parset[@name='{self.root_name}']")
        if parset is None:
            raise ValueError(f"Could not find parset with name {self.root_name}")
            
        # Update values
        for field in fields(self):
            if field.name in ['filename', 'root_name', 'parent']:
                continue
                
            value = getattr(self, field.name)
            par = parset.find(f"./par[@name='{field.name}']")
            
            if par is not None:
                type_str, value_str = self.set_type(value, field.type)
                par.text = value_str
                par.set('type', type_str)
        
        # Save updates
        tree.write(xml_path, encoding='utf-8', xml_declaration=True)

    def update(self, **kwargs) -> None:
        """Update instance attributes
        
        Args:
            **kwargs: Attribute names and values to update
        """
        for key, value in kwargs.items():
            if not hasattr(self, key):
                raise ValueError(f"Invalid attribute: {key}")
            setattr(self, key, value)

    def delete(self, xml_path: Optional[Path] = None) -> None:
        """Delete XML file for this instance
        
        Args:
            xml_path: Optional override for the default filename
        """
        if xml_path is None:
            xml_path = Path(self.filename)
            
        if xml_path.exists():
            xml_path.unlink()

@dataclass
class TraceHeaderEntry:
    """Individual trace header entry"""
    label: str
    description: str
    format: str
    elementCount: int
    byteOffset: int

@dataclass
class TraceProperties:
    """Trace properties configuration"""
    # Format to type mapping
    FORMAT_TYPES = {
        'INTEGER': np.int32,
        'FLOAT': np.float32,
        'DOUBLE': np.float64,
        'LONG': np.int64,
        'SHORT': np.int16,
        'BYTE': np.int8
    }

    # Format to byte size mapping (derived from numpy dtypes)
    FORMAT_SIZES = {
        'INTEGER': np.dtype(np.int32).itemsize,
        'FLOAT': np.dtype(np.float32).itemsize,
        'DOUBLE': np.dtype(np.float64).itemsize,
        'LONG': np.dtype(np.int64).itemsize,
        'SHORT': np.dtype(np.int16).itemsize,
        'BYTE': np.dtype(np.int8).itemsize
    }

    entries: List[TraceHeaderEntry] = field(default_factory=lambda: [
        TraceHeaderEntry(
            label="SEQNO",
            description="Sequence number in ensemble",
            format="INTEGER",
            elementCount=1,
            byteOffset=0
        ),
        TraceHeaderEntry(
            label="END_ENS",
            description="End-of-ensemble flag*",
            format="INTEGER",
            elementCount=1,
            byteOffset=4
        ),
        TraceHeaderEntry(
            label="EOJ",
            description="End of job flag*",
            format="INTEGER",
            elementCount=1,
            byteOffset=8
        ),
        TraceHeaderEntry(
            label="TRACENO",
            description="Trace number in seismic line*",
            format="INTEGER",
            elementCount=1,
            byteOffset=12
        ),
        TraceHeaderEntry(
            label="TRC_TYPE",
            description="Trace type (data, aux, etc.)",
            format="INTEGER",
            elementCount=1,
            byteOffset=16
        ),
        TraceHeaderEntry(
            label="TLIVE_S",
            description="Start time of live samples",
            format="FLOAT",
            elementCount=1,
            byteOffset=20
        ),
        TraceHeaderEntry(
            label="TFULL_S",
            description="Start time of full samples",
            format="FLOAT",
            elementCount=1,
            byteOffset=24
        ),
        TraceHeaderEntry(
            label="TFULL_E",
            description="End time of full samples",
            format="FLOAT",
            elementCount=1,
            byteOffset=28
        ),
        TraceHeaderEntry(
            label="TLIVE_E",
            description="End time of live samples",
            format="FLOAT",
            elementCount=1,
            byteOffset=32
        ),
        TraceHeaderEntry(
            label="LEN_SURG",
            description="Length of surgical mute taper",
            format="FLOAT",
            elementCount=1,
            byteOffset=36
        ),
        TraceHeaderEntry(
            label="TOT_STAT",
            description="Total static for this trace",
            format="FLOAT",
            elementCount=1,
            byteOffset=40
        ),
        TraceHeaderEntry(
            label="NA_STAT",
            description="Portion of static not applied",
            format="FLOAT",
            elementCount=1,
            byteOffset=44
        ),
        TraceHeaderEntry(
            label="AMP_NORM",
            description="Amplitude normalization factor",
            format="FLOAT",
            elementCount=1,
            byteOffset=48
        ),
        TraceHeaderEntry(
            label="TR_FOLD",
            description="Actual trace fold",
            format="FLOAT",
            elementCount=1,
            byteOffset=52
        ),
        TraceHeaderEntry(
            label="SKEWSTAT",
            description="Multiplex skew static",
            format="FLOAT",
            elementCount=1,
            byteOffset=56
        ),
        TraceHeaderEntry(
            label="LINE_NO",
            description="Line number (hased line name)*",
            format="INTEGER",
            elementCount=1,
            byteOffset=60
        ),
        TraceHeaderEntry(
            label="LSEG_END",
            description="Line segment end*",
            format="INTEGER",
            elementCount=1,
            byteOffset=64
        ),
        TraceHeaderEntry(
            label="LSEG_SEQ",
            description="Line segment sequence number*",
            format="INTEGER",
            elementCount=1,
            byteOffset=68
        )
    ])
    _label_map: Dict[str, TraceHeaderEntry] = field(init=False)

    # Metadata fields
    root_name: str = "TraceProperties"
    parent: str = "JavaSeis Metadata"
    filename: str = "FileProperties.xml"

    def __post_init__(self):
        """Create label map after initialization"""
        self._label_map = {entry.label: entry for entry in self.entries}

    def add_entry(self, entry: TraceHeaderEntry) -> None:
        """Add a new trace header entry and remap"""
        if entry.label in self._label_map:
            raise ValueError(f"Entry with label {entry.label} already exists")
        self.entries.append(entry)
        self._label_map[entry.label] = entry
        self.remap()

    def get_entry(self, label: str) -> Optional[TraceHeaderEntry]:
        """Get trace header entry by label"""
        return self._label_map.get(label)

    def replace_entry(self, entry: TraceHeaderEntry) -> None:
        """Replace an existing trace header entry
        
        Args:
            entry: New TraceHeaderEntry to replace existing one with same label
            
        Raises:
            ValueError: If entry with label doesn't exist
        """
        if entry.label not in self._label_map:
            raise ValueError(f"Entry with label {entry.label} does not exist")
            
        self.delete_entry(entry.label)
        self.add_entry(entry)

    def delete_entry(self, label: str) -> bool:
        """Delete trace header entry by label and remap"""
        entry = self._label_map.get(label)
        if entry:
            self.entries.remove(entry)
            del self._label_map[label]
            self.remap()
            return True
        return False

    def remap(self) -> None:
        """Regenerate label map, sort entries, and recalculate byte offsets
        
        1. Regenerates the label map
        2. Sorts entries alphabetically by label
        3. Reorders the entries list to match
        4. Recalculates byte offsets based on format type and element count
        """
        # Regenerate map
        self._label_map = {entry.label: entry for entry in self.entries}
        
        # Sort labels alphabetically
        sorted_labels = sorted(self._label_map.keys())
        
        # Reorder entries list based on sorted labels
        self.entries = [self._label_map[label] for label in sorted_labels]
        
        # Recalculate byte offsets based on format type
        current_offset = 0
        for entry in self.entries:
            entry.byteOffset = current_offset
            # Get byte size for format type
            byte_size = self.FORMAT_SIZES.get(entry.format, 4)  # Default to 4 bytes if unknown
            # Calculate total bytes for this entry
            current_offset += byte_size * entry.elementCount

    def from_xml(self, xml_path: Optional[Path] = None) -> None:
        """Read entries from XML file
        
        Args:
            xml_path: Optional override for the default filename
        """
        if xml_path is None:
            xml_path = Path(self.filename)
        
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # Find TraceProperties parset
        parset = root.find(f".//parset[@name='TraceProperties']")
        if parset is None:
            raise ValueError("Could not find TraceProperties parset")
        
        # Clear existing entries
        new_entries = []
        
        # Process each entry_N parset
        for entry_parset in parset.findall("parset"):
            # Get parameters from the entry parset
            label = entry_parset.find(".//par[@name='label']").text.strip()
            description = entry_parset.find(".//par[@name='description']").text.strip()
            format_type = entry_parset.find(".//par[@name='format']").text.strip()
            element_count = int(entry_parset.find(".//par[@name='elementCount']").text)
            byte_offset = int(entry_parset.find(".//par[@name='byteOffset']").text)
            
            new_entry = TraceHeaderEntry(
                label=label,
                description=description,
                format=format_type,
                elementCount=element_count,
                byteOffset=byte_offset
            )
            new_entries.append(new_entry)
            
        # Update entries list with parsed results
        self.entries = new_entries
        self._label_map = {entry.label: entry for entry in self.entries}

    def to_xml(self, xml_path: Optional[Path] = None) -> None:
        """Write entries to XML file"""
        if xml_path is None:
            xml_path = Path(self.filename)
        #remap to ensure everything is in order
        self.remap()
        root = ET.Element('parset', name=self.parent)
        parset = ET.SubElement(root, 'parset', name=self.root_name)
        
        for entry in self.entries:
            e = ET.SubElement(parset, 'entry')
            e.set('label', entry.label)
            e.set('description', entry.description)
            e.set('format', entry.format)
            e.set('elementCount', str(entry.elementCount))
            e.set('byteOffset', str(entry.byteOffset))
            
        tree = ET.ElementTree(root)
        tree.write(xml_path, encoding='utf-8', xml_declaration=True)

    def update_xml(self, xml_path: Optional[Path] = None) -> None:
        """Update trace properties in existing XML file
        
        Args:
            xml_path: Optional override for the default filename
        """
        if xml_path is None:
            xml_path = Path(self.filename)
            
        # Ensure everything is in order
        self.remap()
        
        # Parse existing XML
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # Find the TraceProperties parset
        parset = root.find(f".//parset[@name='{self.root_name}']")
        if parset is None:
            raise ValueError(f"Could not find parset with name {self.root_name}")
        
        # Remove all existing entries
        for entry in parset.findall(".//entry"):
            parset.remove(entry)
        
        # Add current entries
        for entry in self.entries:
            e = ET.SubElement(parset, 'entry')
            e.set('label', entry.label)
            e.set('description', entry.description)
            e.set('format', entry.format)
            e.set('elementCount', str(entry.elementCount))
            e.set('byteOffset', str(entry.byteOffset))
        
        # Write back to file
        tree.write(xml_path, encoding='utf-8', xml_declaration=True)

@dataclass(order=True)
class VirtualFolders(XMLDataclass):
    """Virtual folders configuration"""
    NDIR: np.int32 = np.int32(1)
    FILESYSTEM_0: str = ".,READ_WRITE"
    Version: str = "2006.2"
    Header: str = "VFIO org.javaseis.io.VirtualFolder 2006.2"
    Type: str = "SS"
    POLICY_ID: Policy = Policy.RANDOM
    GLOBAL_REQUIRED_FREE_SPACE: Optional[np.int64] = None
    
    # Metadata fields
    filename: str = "VirtualFolders.xml"
    root_name: str = "VirtualFolders"
    parent: str = None



@dataclass(order=True)
class TraceFile(XMLDataclass):
    """Trace data extent configuration"""
    """Base class for extent management"""
    VFIO_VERSION: str = "2006.2"
    VFIO_EXTSIZE: Optional[np.int64] = None
    VFIO_MAXFILE: Optional[np.int32] = None
    VFIO_MAXPOS: Optional[np.int64] = None
    VFIO_EXTNAME: str = "TraceFile"
    VFIO_POLICY: Policy = Policy.RANDOM
    
    # Metadata fields
    root_name: str = "ExtentManager"
    parent: str = None
    filename: str = "TraceFile.xml"

@dataclass(order=True)
class TraceHeaders(XMLDataclass):
    """Trace headers extent configuration"""
    """Base class for extent management"""
    VFIO_VERSION: str = "2006.2"
    VFIO_EXTSIZE: Optional[np.int64] = None
    VFIO_MAXFILE: Optional[np.int32] = None
    VFIO_MAXPOS: Optional[np.int64] = None
    VFIO_EXTNAME: str = "TraceHeaders"
    VFIO_POLICY: Policy = Policy.RANDOM
    
    # Metadata fields
    root_name: str = "ExtentManager"
    parent: str = None
    filename: str = "TraceHeaders.xml"

@dataclass
class FieldInstruments(XMLDataclass):
    """Field instrument configuration"""
    systemFormatCode: np.int32 = np.int32(2139081118)
    nAuxChannels: np.int32 = np.int32(2139081118)
    systemSerialNum: np.int32 = np.int32(2139081118)
    earlyGain: np.float32 = np.float32(0.0)
    systemDialinConst: np.float32 = np.float32(3.4E38)
    systemManCode: np.int32 = np.int32(2139081118)
    notchFiltFreq: np.float32 = np.float32(0.0)
    highcutFiltSlope: np.float32 = np.float32(0.0)
    lowcutFiltFreq: np.float32 = np.float32(0.0)
    preampGain: np.float32 = np.float32(0.0)
    notchFiltSlope: np.float32 = np.float32(0.0)
    gainMode: np.int32 = np.int32(0)
    originalSamprat: np.float32 = np.float32(0.0)
    highcutFiltFreq: np.float32 = np.float32(0.0)
    originalNumsmp: np.int32 = np.int32(2001)
    aaFiltFreq: np.float32 = np.float32(0.0)
    sourceType: np.int32 = np.int32(2139081118)
    dateRecorded: np.int32 = np.int32(0)
    lowcutFiltSlope: np.float32 = np.float32(0.0)
    aaFiltSlope: np.float32 = np.float32(0.0)
    
    # Metadata fields
    root_name: str = "FieldInstruments"
    parent: str = "CustomProperties"
    filename: str = "FileProperties.xml"

@dataclass
class Geometry(XMLDataclass):
    """Geometry configuration"""
    minCdpExternal: np.int32 = np.int32(0)
    nOffsetBins: np.int32 = np.int32(2139081118)
    nCrosslinesExternal: np.int32 = np.int32(0)
    ntracesTotal: np.int64 = np.int64(2139081118)
    nCdps: np.int32 = np.int32(1002)
    maxSin: np.int32 = np.int32(2139081118)
    incChan: np.int32 = np.int32(2139081118)
    ySurfLoc1: np.float64 = np.float64(3.3999999521443642E38)
    offsetMax: np.float32 = np.float32(3.4E38)
    units: np.int32 = np.int32(3)
    incCdpExternal: np.int32 = np.int32(0)
    xXLine1End: np.float32 = np.float32(0.0)
    yILine1End: np.float32 = np.float32(0.0)
    marine: np.int32 = np.int32(0)
    dCdpILine: np.float32 = np.float32(25.0)
    nInlinesExternal: np.int32 = np.int32(0)
    maxSurfLoc: np.int32 = np.int32(2139081118)
    multiComp: np.int32 = np.int32(0)
    maxNtrSource: np.int32 = np.int32(2139081118)
    maxILine: np.int32 = np.int32(1)
    xILine1Start: np.float32 = np.float32(0.0)
    cdpsAssigned: np.int32 = np.int32(0)
    dCdpXLine: np.float32 = np.float32(500.0)
    nILines: np.int32 = np.int32(2)
    incOffsetBin: np.int32 = np.int32(2139081118)
    minCdp: np.int32 = np.int32(1)
    nSurfLocs: np.int32 = np.int32(2139081118)
    offsetBinDist: np.float32 = np.float32(3.4E38)
    maxXLine: np.int32 = np.int32(500)
    finalDatum: np.float32 = np.float32(3.4E38)
    yXLine1End: np.float32 = np.float32(500.0)
    geomAssigned: np.int32 = np.int32(0)
    yRef: np.float64 = np.float64(0.0)
    incCdp: np.int32 = np.int32(1)
    datumVel: np.float32 = np.float32(3.4E38)
    azimuth: np.float64 = np.float64(90.0)
    xSurfLoc1: np.float64 = np.float64(3.3999999521443642E38)
    nXLines: np.int32 = np.int32(501)
    nLiveGroups: np.int32 = np.int32(2139081118)
    incSurfLoc: np.int32 = np.int32(2139081118)
    maxNtrCdp: np.int32 = np.int32(2139081118)
    maxCdp: np.int32 = np.int32(1002)
    maxOffsetBin: np.int32 = np.int32(2139081118)
    maxNtrRec: np.int32 = np.int32(2139081118)
    minILine: np.int32 = np.int32(0)
    maxChan: np.int32 = np.int32(2139081118)
    minChan: np.int32 = np.int32(2139081118)
    xRef: np.float64 = np.float64(0.0)
    xILine1End: np.float32 = np.float32(12500.0)
    minOffsetBin: np.int32 = np.int32(2139081118)
    nLiveShots: np.int32 = np.int32(2139081118)
    minXLine: np.int32 = np.int32(0)
    minSurfLoc: np.int32 = np.int32(2139081118)
    threeD: np.int32 = np.int32(1)
    yILine1Start: np.float32 = np.float32(0.0)

    # Metadata fields
    root_name: str = "Geometry"
    parent: str = "CustomProperties"
    filename: str = "FileProperties.xml"

@dataclass
class CustomProperties(XMLDataclass):
    """Custom properties configuration"""
    Synthetic: bool = False
    SecondaryKey: str = "SEQNO"
    GeomMatchesFlag: np.int32 = np.int32(1)
    PrimaryKey: str = "FRAME"
    PrimarySort: str = "inline"
    TraceNoMatchesFlag: np.int32 = np.int32(0)
    Stacked: bool = True
    cookie: np.int32 = np.int32(2003122)
    FieldInstruments: FieldInstruments = field(default_factory=FieldInstruments)
    Geometry: Geometry = field(default_factory=Geometry)

    # Metadata fields
    root_name: str = "CustomProperties"
    parent: str = "JavaSeis Metadata"
    filename: str = "FileProperties.xml"

@dataclass
class FileProperties(XMLDataclass):
    """File properties configuration"""
    Comments: str = "www.javaseis.org - JavaSeis File Properties 2006.3"
    JavaSeisVersion: str = "2006.3"
    DataType: str = "UNKNOWN"
    TraceFormat: str = "COMPRESSED_INT16"
    ByteOrder: str = "LITTLE_ENDIAN"
    Mapped: bool = True
    DataDimensions: np.int32 = np.int32(3)
    AxisLabels: List[str] = field(default_factory=lambda: ["TIME", "TRACE", "FRAME"])
    AxisUnits: List[str] = field(default_factory=lambda: ["milliseconds", "meters", "meters"])
    AxisDomains: List[str] = field(default_factory=lambda: ["time", "space", "space"])
    AxisLengths: List[np.int64] = field(default_factory=lambda: [np.int64(0), np.int64(0), np.int64(0)])
    LogicalOrigins: List[np.int64] = field(default_factory=lambda: [np.int64(0), np.int64(0), np.int64(0)])
    LogicalDeltas: List[np.float64] = field(default_factory=lambda: [np.float64(1.0), np.float64(1.0), np.float64(1.0)])
    PhysicalOrigins: List[np.float64] = field(default_factory=lambda: [np.float64(0.0), np.float64(0.0), np.float64(0.0)])
    PhysicalDeltas: List[np.float64] = field(default_factory=lambda: [np.float64(1.0), np.float64(1.0), np.float64(1.0)])
    HeaderLengthBytes: np.int32 = np.int32(68)

    # Metadata fields
    root_name: str = "FileProperties"
    parent: str = "JavaSeis Metadata"
    filename: str = "FileProperties.xml"


