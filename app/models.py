from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from decimal import Decimal
from enum import Enum


# Enums for better type safety
class UserRole(str, Enum):
    ADMIN = "admin"
    STAFF = "staff"


class AssetCondition(str, Enum):
    BAIK = "baik"
    RUSAK_RINGAN = "rusak_ringan"
    RUSAK_BERAT = "rusak_berat"
    HILANG = "hilang"


class MovementType(str, Enum):
    MASUK = "masuk"
    KELUAR = "keluar"
    MUTASI = "mutasi"


# Persistent models (stored in database)
class User(SQLModel, table=True):
    __tablename__ = "users"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, max_length=50)
    email: str = Field(unique=True, max_length=255, regex=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    full_name: str = Field(max_length=100)
    password_hash: str = Field(max_length=255)
    role: UserRole = Field(default=UserRole.STAFF)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    created_assets: List["Asset"] = Relationship(back_populates="created_by_user")
    updated_assets: List["Asset"] = Relationship(back_populates="updated_by_user")
    asset_movements: List["AssetMovement"] = Relationship(back_populates="user")


class Location(SQLModel, table=True):
    __tablename__ = "locations"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    kode_lokasi: str = Field(unique=True, max_length=20)
    nama_lokasi: str = Field(max_length=100)
    deskripsi: str = Field(default="", max_length=500)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    assets: List["Asset"] = Relationship(back_populates="location")
    rooms: List["Room"] = Relationship(back_populates="location")


class Room(SQLModel, table=True):
    __tablename__ = "rooms"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    nama_ruang: str = Field(max_length=100)
    location_id: int = Field(foreign_key="locations.id")
    deskripsi: str = Field(default="", max_length=500)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    location: Location = Relationship(back_populates="rooms")
    assets: List["Asset"] = Relationship(back_populates="room")


class AssetCategory(SQLModel, table=True):
    __tablename__ = "asset_categories"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    kode_kategori: str = Field(unique=True, max_length=20)
    nama_kategori: str = Field(max_length=100)
    deskripsi: str = Field(default="", max_length=500)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    assets: List["Asset"] = Relationship(back_populates="category")


class Asset(SQLModel, table=True):
    __tablename__ = "assets"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)

    # Core identification fields
    kode: str = Field(unique=True, max_length=50, description="Kode unik aset")
    barcode: Optional[str] = Field(default=None, unique=True, max_length=50, description="Barcode untuk scanning")
    nomor_aset: str = Field(unique=True, max_length=50, description="Nomor aset resmi")

    # Asset details
    nama_barang: str = Field(max_length=200, description="Nama lengkap barang")
    merk_tipe: str = Field(max_length=100, description="Merk dan tipe barang")
    kode_barang: str = Field(max_length=50, description="Kode klasifikasi barang")

    # Financial information
    tahun_anggaran: int = Field(description="Tahun anggaran pembelian")
    rupiah_satuan: Decimal = Field(max_digits=15, decimal_places=2, description="Nilai satuan dalam rupiah")
    tanggal_perolehan: date = Field(description="Tanggal perolehan barang")

    # Location and assignment
    location_id: int = Field(foreign_key="locations.id")
    room_id: Optional[int] = Field(default=None, foreign_key="rooms.id")
    pemegang_barang: str = Field(max_length=100, description="Nama pemegang/penanggungjawab barang")

    # Asset status and condition
    kondisi_barang: AssetCondition = Field(default=AssetCondition.BAIK)
    category_id: Optional[int] = Field(default=None, foreign_key="asset_categories.id")

    # Additional information
    gambar: Optional[str] = Field(default=None, max_length=500, description="Path/URL gambar barang")
    keterangan: str = Field(default="", max_length=1000, description="Keterangan tambahan")
    spesifikasi: Dict[str, Any] = Field(default={}, sa_column=Column(JSON), description="Spesifikasi teknis dalam JSON")

    # Audit fields
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: int = Field(foreign_key="users.id")
    updated_by: int = Field(foreign_key="users.id")

    # Relationships
    location: Location = Relationship(back_populates="assets")
    room: Optional[Room] = Relationship(back_populates="assets")
    category: Optional[AssetCategory] = Relationship(back_populates="assets")
    created_by_user: User = Relationship(
        back_populates="created_assets", sa_relationship_kwargs={"foreign_keys": "[Asset.created_by]"}
    )
    updated_by_user: User = Relationship(
        back_populates="updated_assets", sa_relationship_kwargs={"foreign_keys": "[Asset.updated_by]"}
    )
    movements: List["AssetMovement"] = Relationship(back_populates="asset")
    maintenance_records: List["MaintenanceRecord"] = Relationship(back_populates="asset")


class AssetMovement(SQLModel, table=True):
    __tablename__ = "asset_movements"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    asset_id: int = Field(foreign_key="assets.id")
    movement_type: MovementType = Field(description="Jenis pergerakan: masuk/keluar/mutasi")

    # Location information
    from_location_id: Optional[int] = Field(default=None, foreign_key="locations.id")
    to_location_id: Optional[int] = Field(default=None, foreign_key="locations.id")
    from_room_id: Optional[int] = Field(default=None, foreign_key="rooms.id")
    to_room_id: Optional[int] = Field(default=None, foreign_key="rooms.id")

    # Movement details
    tanggal_movement: datetime = Field(default_factory=datetime.utcnow)
    keterangan: str = Field(default="", max_length=500)
    dokumen_referensi: Optional[str] = Field(default=None, max_length=100, description="Nomor dokumen referensi")

    # Person responsible
    pemegang_lama: Optional[str] = Field(default=None, max_length=100)
    pemegang_baru: Optional[str] = Field(default=None, max_length=100)

    # Audit
    user_id: int = Field(foreign_key="users.id", description="User yang melakukan pergerakan")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    asset: Asset = Relationship(back_populates="movements")
    user: User = Relationship(back_populates="asset_movements")


class MaintenanceRecord(SQLModel, table=True):
    __tablename__ = "maintenance_records"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    asset_id: int = Field(foreign_key="assets.id")

    tanggal_maintenance: date = Field(description="Tanggal pemeliharaan")
    jenis_maintenance: str = Field(max_length=100, description="Jenis pemeliharaan")
    deskripsi: str = Field(max_length=1000, description="Deskripsi pekerjaan maintenance")
    biaya: Optional[Decimal] = Field(default=None, max_digits=15, decimal_places=2, description="Biaya maintenance")
    teknisi: str = Field(max_length=100, description="Nama teknisi/pelaksana")

    kondisi_sebelum: AssetCondition = Field(description="Kondisi sebelum maintenance")
    kondisi_sesudah: AssetCondition = Field(description="Kondisi setelah maintenance")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: int = Field(foreign_key="users.id")

    # Relationships
    asset: Asset = Relationship(back_populates="maintenance_records")


# Non-persistent schemas (for validation, forms, API requests/responses)
class UserCreate(SQLModel, table=False):
    username: str = Field(max_length=50)
    email: str = Field(max_length=255)
    full_name: str = Field(max_length=100)
    password: str = Field(min_length=6)
    role: UserRole = Field(default=UserRole.STAFF)


class UserUpdate(SQLModel, table=False):
    username: Optional[str] = Field(default=None, max_length=50)
    email: Optional[str] = Field(default=None, max_length=255)
    full_name: Optional[str] = Field(default=None, max_length=100)
    role: Optional[UserRole] = Field(default=None)
    is_active: Optional[bool] = Field(default=None)


class LocationCreate(SQLModel, table=False):
    kode_lokasi: str = Field(max_length=20)
    nama_lokasi: str = Field(max_length=100)
    deskripsi: str = Field(default="", max_length=500)


class LocationUpdate(SQLModel, table=False):
    kode_lokasi: Optional[str] = Field(default=None, max_length=20)
    nama_lokasi: Optional[str] = Field(default=None, max_length=100)
    deskripsi: Optional[str] = Field(default=None, max_length=500)
    is_active: Optional[bool] = Field(default=None)


class RoomCreate(SQLModel, table=False):
    nama_ruang: str = Field(max_length=100)
    location_id: int
    deskripsi: str = Field(default="", max_length=500)


class RoomUpdate(SQLModel, table=False):
    nama_ruang: Optional[str] = Field(default=None, max_length=100)
    location_id: Optional[int] = Field(default=None)
    deskripsi: Optional[str] = Field(default=None, max_length=500)
    is_active: Optional[bool] = Field(default=None)


class AssetCategoryCreate(SQLModel, table=False):
    kode_kategori: str = Field(max_length=20)
    nama_kategori: str = Field(max_length=100)
    deskripsi: str = Field(default="", max_length=500)


class AssetCategoryUpdate(SQLModel, table=False):
    kode_kategori: Optional[str] = Field(default=None, max_length=20)
    nama_kategori: Optional[str] = Field(default=None, max_length=100)
    deskripsi: Optional[str] = Field(default=None, max_length=500)
    is_active: Optional[bool] = Field(default=None)


class AssetCreate(SQLModel, table=False):
    kode: str = Field(max_length=50)
    barcode: Optional[str] = Field(default=None, max_length=50)
    nomor_aset: str = Field(max_length=50)
    nama_barang: str = Field(max_length=200)
    merk_tipe: str = Field(max_length=100)
    kode_barang: str = Field(max_length=50)
    tahun_anggaran: int
    rupiah_satuan: Decimal
    tanggal_perolehan: date
    location_id: int
    room_id: Optional[int] = Field(default=None)
    pemegang_barang: str = Field(max_length=100)
    kondisi_barang: AssetCondition = Field(default=AssetCondition.BAIK)
    category_id: Optional[int] = Field(default=None)
    gambar: Optional[str] = Field(default=None, max_length=500)
    keterangan: str = Field(default="", max_length=1000)
    spesifikasi: Dict[str, Any] = Field(default={})


class AssetUpdate(SQLModel, table=False):
    kode: Optional[str] = Field(default=None, max_length=50)
    barcode: Optional[str] = Field(default=None, max_length=50)
    nomor_aset: Optional[str] = Field(default=None, max_length=50)
    nama_barang: Optional[str] = Field(default=None, max_length=200)
    merk_tipe: Optional[str] = Field(default=None, max_length=100)
    kode_barang: Optional[str] = Field(default=None, max_length=50)
    tahun_anggaran: Optional[int] = Field(default=None)
    rupiah_satuan: Optional[Decimal] = Field(default=None)
    tanggal_perolehan: Optional[date] = Field(default=None)
    location_id: Optional[int] = Field(default=None)
    room_id: Optional[int] = Field(default=None)
    pemegang_barang: Optional[str] = Field(default=None, max_length=100)
    kondisi_barang: Optional[AssetCondition] = Field(default=None)
    category_id: Optional[int] = Field(default=None)
    gambar: Optional[str] = Field(default=None, max_length=500)
    keterangan: Optional[str] = Field(default=None, max_length=1000)
    spesifikasi: Optional[Dict[str, Any]] = Field(default=None)
    is_active: Optional[bool] = Field(default=None)


class AssetMovementCreate(SQLModel, table=False):
    asset_id: int
    movement_type: MovementType
    from_location_id: Optional[int] = Field(default=None)
    to_location_id: Optional[int] = Field(default=None)
    from_room_id: Optional[int] = Field(default=None)
    to_room_id: Optional[int] = Field(default=None)
    tanggal_movement: datetime = Field(default_factory=datetime.utcnow)
    keterangan: str = Field(default="", max_length=500)
    dokumen_referensi: Optional[str] = Field(default=None, max_length=100)
    pemegang_lama: Optional[str] = Field(default=None, max_length=100)
    pemegang_baru: Optional[str] = Field(default=None, max_length=100)


class MaintenanceRecordCreate(SQLModel, table=False):
    asset_id: int
    tanggal_maintenance: date
    jenis_maintenance: str = Field(max_length=100)
    deskripsi: str = Field(max_length=1000)
    biaya: Optional[Decimal] = Field(default=None)
    teknisi: str = Field(max_length=100)
    kondisi_sebelum: AssetCondition
    kondisi_sesudah: AssetCondition


class MaintenanceRecordUpdate(SQLModel, table=False):
    tanggal_maintenance: Optional[date] = Field(default=None)
    jenis_maintenance: Optional[str] = Field(default=None, max_length=100)
    deskripsi: Optional[str] = Field(default=None, max_length=1000)
    biaya: Optional[Decimal] = Field(default=None)
    teknisi: Optional[str] = Field(default=None, max_length=100)
    kondisi_sebelum: Optional[AssetCondition] = Field(default=None)
    kondisi_sesudah: Optional[AssetCondition] = Field(default=None)


# Response schemas for API
class AssetResponse(SQLModel, table=False):
    id: int
    kode: str
    barcode: Optional[str]
    nomor_aset: str
    nama_barang: str
    merk_tipe: str
    kode_barang: str
    tahun_anggaran: int
    rupiah_satuan: Decimal
    tanggal_perolehan: str  # Will be converted from date
    pemegang_barang: str
    kondisi_barang: AssetCondition
    gambar: Optional[str]
    keterangan: str
    location_name: str
    room_name: Optional[str]
    category_name: Optional[str]
    created_at: str  # Will be converted from datetime
    updated_at: str  # Will be converted from datetime


class LocationSummary(SQLModel, table=False):
    location_id: int
    kode_lokasi: str
    nama_lokasi: str
    total_assets: int
    assets_by_condition: Dict[str, int]


class MovementReport(SQLModel, table=False):
    period_start: str
    period_end: str
    total_masuk: int
    total_keluar: int
    total_mutasi: int
    movements_by_location: Dict[str, Dict[str, int]]
