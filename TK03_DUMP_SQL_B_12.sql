CREATE SCHEMA IF NOT EXISTS SIZOPI;
SET search_path TO SIZOPI;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";


CREATE TABLE PENGGUNA (
    username        VARCHAR(50) PRIMARY KEY,
    email           VARCHAR(100) NOT NULL,
    password        VARCHAR(50)  NOT NULL,
    nama_depan      VARCHAR(50)  NOT NULL,
    nama_tengah     VARCHAR(50),
    nama_belakang   VARCHAR(50)  NOT NULL,
    no_telepon      VARCHAR(15)  NOT NULL
);

CREATE TABLE PENGUNJUNG (
    username_p      VARCHAR(50)  PRIMARY KEY,
    alamat          VARCHAR(200) NOT NULL,
    tgl_lahir       DATE         NOT NULL,
    FOREIGN KEY (username_p) REFERENCES PENGGUNA(username)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE DOKTER_HEWAN (
    username_DH     VARCHAR(50)  PRIMARY KEY,
    no_STR          VARCHAR(50)  NOT NULL,
    FOREIGN KEY (username_DH) REFERENCES PENGGUNA(username)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE SPESIALISASI (
    username_SH     VARCHAR(50),
    nama_spesialis  VARCHAR(100) NOT NULL,
    PRIMARY KEY (username_SH, nama_spesialis),
    FOREIGN KEY (username_SH) REFERENCES DOKTER_HEWAN(username_DH)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE PENJAGA_HEWAN (
    username_jh     VARCHAR(50)  PRIMARY KEY,
    id_staf         UUID         NOT NULL DEFAULT uuid_generate_v4(),
    FOREIGN KEY (username_jh) REFERENCES PENGGUNA(username)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE PELATIH_HEWAN (
    username_lh     VARCHAR(50)  PRIMARY KEY,
    id_staf         UUID         NOT NULL DEFAULT uuid_generate_v4(),
    FOREIGN KEY (username_lh) REFERENCES PENGGUNA(username)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE STAF_ADMIN (
    username_sa     VARCHAR(50)  PRIMARY KEY,
    id_staf         UUID         NOT NULL DEFAULT uuid_generate_v4(),
    FOREIGN KEY (username_sa) REFERENCES PENGGUNA(username)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE HABITAT (
    nama            VARCHAR(50)  PRIMARY KEY,
    luas_area       DECIMAL      NOT NULL,
    kapasitas       INT          NOT NULL,
    status          VARCHAR(100) NOT NULL
);

CREATE TABLE HEWAN (
    id              UUID         PRIMARY KEY DEFAULT uuid_generate_v4(),
    nama            VARCHAR(100),
    spesies         VARCHAR(100) NOT NULL,
    asal_hewan      VARCHAR(100) NOT NULL,
    tanggal_lahir   DATE,
    status_kesehatan VARCHAR(50) NOT NULL,
    nama_habitat    VARCHAR(50)  NOT NULL,
    url_foto        VARCHAR(255) NOT NULL,
    FOREIGN KEY (nama_habitat) REFERENCES HABITAT(nama)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE CATATAN_MEDIS (
    id_hewan               UUID      NOT NULL,
    username_dh            VARCHAR(50) NOT NULL,
    tanggal_pemeriksaan    DATE      NOT NULL,
    diagnosis              VARCHAR(100),
    pengobatan             VARCHAR(100),
    status_kesehatan       VARCHAR(50) NOT NULL,
    catatan_tindak_lanjut  VARCHAR(100),
    PRIMARY KEY (id_hewan, tanggal_pemeriksaan),
    FOREIGN KEY (id_hewan) REFERENCES HEWAN(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (username_dh) REFERENCES DOKTER_HEWAN(username_DH)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE PAKAN (
    id_hewan       UUID      NOT NULL,
    jadwal         TIMESTAMP NOT NULL,
    jenis          VARCHAR(50) NOT NULL,
    jumlah         INT        NOT NULL,
    status         VARCHAR(50) NOT NULL,
    PRIMARY KEY (id_hewan, jadwal),
    FOREIGN KEY (id_hewan) REFERENCES HEWAN(id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE MEMBERI (
    id_hewan     UUID      NOT NULL,
    jadwal       TIMESTAMP NOT NULL,
    username_jh  VARCHAR(50),
    PRIMARY KEY (id_hewan, username_jh, jadwal),
    FOREIGN KEY (id_hewan) REFERENCES HEWAN(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (username_jh) REFERENCES PENJAGA_HEWAN(username_jh)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE FASILITAS (
    nama           VARCHAR(50) PRIMARY KEY,
    jadwal         TIMESTAMP   NOT NULL,
    kapasitas_max  INT         NOT NULL
);

CREATE TABLE ATRAKSI (
    nama_atraksi VARCHAR(50) PRIMARY KEY,
    lokasi       VARCHAR(100) NOT NULL,
    FOREIGN KEY (nama_atraksi) REFERENCES FASILITAS(nama)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE JADWAL_PENUGASAN (
    username_lh     VARCHAR(50),
    tgl_penugasan   TIMESTAMP NOT NULL,
    nama_atraksi    VARCHAR(50),
    PRIMARY KEY (username_lh, tgl_penugasan),
    FOREIGN KEY (username_lh) REFERENCES PELATIH_HEWAN(username_lh)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE BERPARTISIPASI (
    nama_fasilitas VARCHAR(50),
    id_hewan       UUID,
    PRIMARY KEY (nama_fasilitas, id_hewan),
    FOREIGN KEY (nama_fasilitas) REFERENCES FASILITAS(nama)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (id_hewan) REFERENCES HEWAN(id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE JADWAL_PEMERIKSAAN_KESEHATAN (
    id_hewan                   UUID NOT NULL,
    tgl_pemeriksaan_selanjutnya DATE NOT NULL,
    freq_pemeriksaan_rutin     INT  NOT NULL,
    PRIMARY KEY (id_hewan, tgl_pemeriksaan_selanjutnya),
    FOREIGN KEY (id_hewan) REFERENCES HEWAN(id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE WAHANA (
    nama_wahana VARCHAR(50) PRIMARY KEY,
    peraturan   TEXT        NOT NULL
);

CREATE TABLE ADOPTER (
    username_adopter VARCHAR(50) UNIQUE,
    id_adopter       UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    total_kontribusi INT         NOT NULL,
    FOREIGN KEY (username_adopter) REFERENCES PENGUNJUNG(username_p)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE INDIVIDU (
    nik        CHAR(16) PRIMARY KEY,
    nama       VARCHAR(100) NOT NULL,
    id_adopter UUID       NOT NULL,
    FOREIGN KEY (id_adopter) REFERENCES ADOPTER(id_adopter)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE ORGANISASI (
    npp              CHAR(8)   PRIMARY KEY,
    nama_organisasi  VARCHAR(100) NOT NULL,
    id_adopter       UUID       NOT NULL,
    FOREIGN KEY (id_adopter) REFERENCES ADOPTER(id_adopter)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE ADOPSI (
    id_adopter             UUID,
    id_hewan               UUID      NOT NULL,
    status_pembayaran      VARCHAR(10) NOT NULL,
    tgl_mulai_adopsi       DATE      NOT NULL,
    tgl_berhenti_adopsi    DATE      NOT NULL,
    kontribusi_finansial   INT       NOT NULL,
    PRIMARY KEY (id_adopter, id_hewan, tgl_mulai_adopsi),
    FOREIGN KEY (id_adopter) REFERENCES ADOPTER(id_adopter)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (id_hewan) REFERENCES HEWAN(id)
        ON DELETE CASCADE ON UPDATE CASCADE
);
