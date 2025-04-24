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

INSERT INTO PENGGUNA VALUES ('user1','user1@example.com','H!4NQpP8','Prasetya',NULL,'Andriani',628156593877.0),
	('user2','user2@example.com','f!8A!cq6','Eva',NULL,'Rajata',628711587141.0),
	('user3','user3@example.com','(W5RgGU9','Ika','Lamar','Maheswara',620112201863.0),
	('user4','user4@example.com','_OZ9NsC(','Endah','Jarwi','Pratama',620352560123.0),
	('user5','user5@example.com','_8Tv(&amp;n(','Bakijan',NULL,'Pertiwi',620300869145.0),
	('user6','user6@example.com','^#6F2bgo','Cakrabirawa','Sakura','Sihombing',628419720767.0),
	('user7','user7@example.com','6T%g5M8v','Jelita',NULL,'Melani',620661093523.0),
	('user8','user8@example.com','masukaja','Raina','Umar','Waluyo',620063812091.0),
	('user9','user9@example.com','password123rahasia','Adiarja','Irsad','Budiman',620142851212.0),
	('user10','user10@example.com','wv_$h4Rk','Bajragin',NULL,'Putra',626940224592.0),
	('user11','user11@example.com',')0BHi9N5','Cengkir',NULL,'Sirait',620654611877.0),
	('user12','user12@example.com','*1gWuYpy','Mahfud',NULL,'Maheswara',621688477931.0),
	('user13','user13@example.com','0$(4p#Sy','Slamet','Caturangga','Uwais',620303921376.0),
	('user14','user14@example.com','@Z9Pcenz','Hamima',NULL,'Maryadi',620926947118.0),
	('user15','user15@example.com','#0pJqMaG','Cahyadi',NULL,'Prasetyo',620896769930.0),
	('user16','user16@example.com',')7n4Kc0v','Galih','Lukita','Mayasari',620762791256.0),
	('user17','user17@example.com','**@6)BOb','Bagus',NULL,'Suryatmi',620979519426.0),
	('user18','user18@example.com','@HF8ZYwg','Langgeng',NULL,'Zulaika',620188684126.0),
	('user19','user19@example.com','@6wkCdOp','Surya',NULL,'Hutasoit',625203519230.0),
	('user20','user20@example.com','_d1XaLNe','Hasan',NULL,'Wahyuni',625744852911.0),
	('user21','user21@example.com','#6Eh9Je)','Farhunnisa','Kania','Samosir',620486296451.0),
	('user22','user22@example.com','%_5fU39q','Jamal',NULL,'Handayani',620266237582.0),
	('user23','user23@example.com','3_1X!APy','Nyana',NULL,'Hariyah',620386401400.0),
	('user24','user24@example.com','h)6O2d^7','Raden',NULL,'Novitasari',620644829838.0),
	('user25','user25@example.com','s8(U6X(y','Danu','Rizki','Usada',620637785707.0),
	('user26','user26@example.com',')3!Q%Alg','Edison','Anastasia','Habibi',624432943161.0),
	('user27','user27@example.com','#KL5Q)Nu','Viman','Mitra','Winarno',620031250239.0),
	('user28','user28@example.com','jrI@8bYj','Legawa',NULL,'Suryatmi',624000250402.0),
	('user29','user29@example.com','_423TmBR','Cagak',NULL,'Aryani',621385334448.0),
	('user30','user30@example.com','$*5Wf$lh','Pranawa',NULL,'Rajasa',620379168602.0),
	('user31','user31@example.com','#*s4Lejk','Jamil','Ana','Prasetya',620912633408.0),
	('user32','user32@example.com','8!T1Mu8g','Diah',NULL,'Aryani',620574922088.0),
	('user33','user33@example.com','yP!2jMed','Oskar','Laras','Usada',627190895773.0),
	('user34','user34@example.com','aOw$8UfW','Lasmanto',NULL,'Budiman',620305357345.0),
	('user35','user35@example.com','%0+@YLs4','Usyi',NULL,'Marpaung',623762542564.0),
	('user36','user36@example.com','g%8RuzG!','Prakosa','Ajiman','Wasita',623028216911.0),
	('user37','user37@example.com','#D*2YTOt','Puspa',NULL,'Utami',626547604842.0),
	('user38','user38@example.com','v#H(9Riz','Humaira','Wakiman','Firmansyah',620319539852.0),
	('user39','user39@example.com',')E0BjSze','Mitra',NULL,'Anggriawan',627493186421.0),
	('user40','user40@example.com','vYS@2Sdj','Fitriani',NULL,'Narpati',620829657081.0),
	('user41','user41@example.com','y+$0L@qU','Ridwan','Raisa','Susanti',620973781327.0),
	('user42','user42@example.com','&amp;jX&amp;#4In','Cager','Simon','Usada',629450678201.0),
	('user43','user43@example.com','^(5$AocB','Carub',NULL,'Pratiwi',622270808621.0),
	('user44','user44@example.com','@7867Fzi','Malik','Laras','Hutasoit',620379378252.0),
	('user45','user45@example.com','(1QWUkFE','Wawan','Ida','Hakim',622059306041.0),
	('user46','user46@example.com',')K2XLAoc','Prayogo',NULL,'Habibi',626151105026.0),
	('user47','user47@example.com','!5O^Ozkp','Patricia','Zahra','Yolanda',621702840065.0),
	('user48','user48@example.com','#NAME?','Galar',NULL,'Pudjiastuti',622353267592.0),
	('user49','user49@example.com','#9A@mPvj','Prasetyo','Julia','Budiman',620695325838.0),
	('user50','user50@example.com','#6s6Sv5N','Raharja',NULL,'Hidayanto',620340956180.0),
	('user51','user51@example.com','e&amp;6DINzd','Purwanto',NULL,'Dongoran',628034295461.0),
	('user52','user52@example.com','I(6)(EBv','Rachel','Bakda','Siregar',622323082751.0),
	('user53','user53@example.com','j7+_1ZnF','Padmi','Kamal','Sitorus',620784661220.0),
	('user54','user54@example.com','#ERROR!','Latika','Mila','Usada',621759473288.0),
	('user55','user55@example.com','#Q03eHUf','Chandra',NULL,'Melani',620196538707.0),
	('user56','user56@example.com','Z%1S8pPr','Pia',NULL,'Jailani',620314251202.0),
	('user57','user57@example.com','!Od6RqDw','Ina','Hasta','Ardianto',620307585114.0),
	('user58','user58@example.com','_+2ja5My','Surya',NULL,'Prasetyo',620556456417.0),
	('user59','user59@example.com','1wO#5GHx','Dimas',NULL,'Hassanah',620580175636.0),
	('user60','user60@example.com','f&amp;1I#w!g','Kasiyah',NULL,'Gunarto',620896182336.0),
	('user61','user61@example.com','!6G#mFCL','Prakosa',NULL,'Kusmawati',629263953682.0),
	('user62','user62@example.com',')sM(D1Wp','Belinda',NULL,'Lazuardi',627086736345.0),
	('user63','user63@example.com','#3O+nj1v','Xanana',NULL,'Kusmawati',620592763673.0),
	('user64','user64@example.com','!1C5SYVv','Gandewa',NULL,'Wijaya',628300023795.0),
	('user65','user65@example.com','J_zrD1Yq','Ikin',NULL,'Wijayanti',623126783505.0),
	('user66','user66@example.com','@63!z_Ss','Artanto','Rosman','Pranowo',626954103909.0),
	('user67','user67@example.com','#7I4dPDm','Devi',NULL,'Uwais',629971876560.0),
	('user68','user68@example.com','_(2Y8eDF','Daruna','Taswir','Sudiati',620045251986.0),
	('user69','user69@example.com',')#o@*8Cs','Jefri',NULL,'Pertiwi',624583375242.0),
	('user70','user70@example.com','j@&amp;@l5Jw','Iriana','Titi','Adriansyah',628861197521.0),
	('user71','user71@example.com','&amp;Z4BaBSy','Lega','Jaya','Utami',620664934587.0),
	('user72','user72@example.com','^2G5AQbx','Usman','Dipa','Anggraini',628374466702.0),
	('user73','user73@example.com','4A^3H#em','Gambira',NULL,'Novitasari',627306268632.0),
	('user74','user74@example.com','p(ss7DeH','Prasetya',NULL,'Nasyidah',629330081731.0),
	('user75','user75@example.com','WDE)A8Ja','Umay','Tina','Mansur',620727455966.0),
	('user76','user76@example.com','J70_%9Hg','Rama','Zulaikha','Mardhiyah',620780347103.0),
	('user77','user77@example.com','0x!3FztW','Danang',NULL,'Rajasa',620551961020.0),
	('user78','user78@example.com','^k3MVIgt','Faizah',NULL,'Saputra',628164593058.0),
	('user79','user79@example.com','X_4^l+Pp','Enteng',NULL,'Sihotang',620274164415.0),
	('user80','user80@example.com','@@0BGytB','Cici',NULL,'Nasyiah',620360096284.0),
	('user81','user81@example.com','(_v0XwoU','Rahmat',NULL,'Waskita',620810422821.0),
	('user82','user82@example.com','U+F6C5Ek','Mulya',NULL,'Ardianto',620268521220.0),
	('user83','user83@example.com','@Eb1HQhi','Sadina',NULL,'Pratiwi',620558039171.0),
	('user84','user84@example.com','$yU8FDAq','Oman','Tedi','Safitri',622078264973.0),
	('user85','user85@example.com','XBC)9VfJ','Asmadi',NULL,'Hasanah',620343895739.0),
	('user86','user86@example.com','6^e3sE3y','Padmi','Rahmi','Maulana',624648356500.0),
	('user87','user87@example.com',')2cJBRoq','Harjo',NULL,'Napitupulu',624987486757.0),
	('user88','user88@example.com','@1pZugW*','Irnanto',NULL,'Wastuti',620962998344.0),
	('user89','user89@example.com',')73EX3eo','Galiono',NULL,'Nashiruddin',628724194930.0),
	('user90','user90@example.com','I+R9VbLa','Edison',NULL,'Pranowo',627458943486.0),
	('user91','user91@example.com','*&amp;1tSJsu','Cahyadi',NULL,'Natsir',626805668289.0),
	('user92','user92@example.com','!U4TG&amp;Ro','Gadang',NULL,'Yolanda',620319661838.0),
	('user93','user93@example.com','$SQ1WQte','Ibrani','Ani','Iswahyudi',620373830237.0),
	('user94','user94@example.com','H)4UAjXn','Warsa',NULL,'Iswahyudi',620307428521.0),
	('user95','user95@example.com','o^1LzgH_','Ciaobella',NULL,'Sinaga',620529296431.0);

INSERT INTO PENGUNJUNG VALUES ('user1','Jalan BKR No. 79, Tangerang Selatan, Papua 17380','1966-05-12 00:00:00'),
	('user2','Gang Stasiun Wonokromo No. 23, Tangerang, Sumatera Utara 73032','2005-03-19 00:00:00'),
	('user3','Jl. Dr. Djunjunan No. 14, Samarinda, Kepulauan Bangka Belitung 01270','1987-12-05 00:00:00'),
	('user4','Gang Asia Afrika No. 33, Semarang, JT 83750','1981-05-10 00:00:00'),
	('user5','Gang Kiaracondong No. 17, Kendari, BB 15270','1990-08-07 00:00:00'),
	('user6','Gang Rawamangun No. 9, Cilegon, AC 16437','1996-05-08 00:00:00'),
	('user7','Gg. Pasteur No. 035, Tarakan, GO 64593','1986-10-18 00:00:00'),
	('user8','Jl. Setiabudhi No. 7, Cirebon, NT 66591','1970-04-15 00:00:00'),
	('user9','Jl. Ahmad Dahlan No. 6, Kendari, RI 60492','1984-10-26 00:00:00'),
	('user10','Jalan Ir. H. Djuanda No. 155, Dumai, KU 97482','1994-11-30 00:00:00'),
	('user11','Jl. Dr. Djunjunan No. 34, Pekalongan, MA 18940','1981-01-15 00:00:00'),
	('user12','Jalan Jend. A. Yani No. 42, Tarakan, Bali 01141','2007-03-16 00:00:00'),
	('user13','Gang Moch. Ramdan No. 98, Denpasar, SN 96934','1987-11-30 00:00:00'),
	('user14','Gang Sentot Alibasa No. 22, Pangkalpinang, MU 57943','1965-09-28 00:00:00'),
	('user15','Jl. Sukajadi No. 9, Purwokerto, Jawa Barat 76775','1965-02-14 00:00:00'),
	('user16','Gg. Gegerkalong Hilir No. 1, Singkawang, Kepulauan Riau 16087','1987-08-20 00:00:00'),
	('user17','Gang Cihampelas No. 8, Batam, Banten 56663','1983-08-01 00:00:00'),
	('user18','Gg. KH Amin Jasuta No. 72, Tangerang, SN 99478','1989-06-20 00:00:00'),
	('user19','Gg. BKR No. 77, Batam, KI 36095','1974-12-05 00:00:00'),
	('user20','Jl. Jend. Sudirman No. 0, Sungai Penuh, Kalimantan Barat 86624','1991-04-26 00:00:00'),
	('user21','Jl. Ronggowarsito No. 117, Tegal, MA 60945','1995-09-14 00:00:00'),
	('user22','Jalan Erlangga No. 4, Metro, DI Yogyakarta 00150','1984-05-11 00:00:00'),
	('user23','Jl. Wonoayu No. 292, Sungai Penuh, JK 08211','1968-10-03 00:00:00'),
	('user24','Gg. Bangka Raya No. 177, Probolinggo, Gorontalo 56821','2006-12-12 00:00:00'),
	('user25','Gg. Soekarno Hatta No. 5, Lhokseumawe, Kalimantan Utara 29654','1988-04-29 00:00:00'),
	('user26','Jl. Ir. H. Djuanda No. 32, Binjai, SB 24420','1976-01-11 00:00:00'),
	('user27','Jl. S. Parman No. 24, Depok, JA 56146','2002-03-28 00:00:00'),
	('user28','Jalan Suniaraja No. 684, Kota Administrasi Jakarta Selatan, BT 15604','1979-09-28 00:00:00'),
	('user29','Jalan Jend. A. Yani No. 39, Padang Sidempuan, Lampung 40092','1986-09-23 00:00:00'),
	('user30','Jl. BKR No. 8, Palu, Sulawesi Tengah 55106','1989-01-22 00:00:00'),
	('user31','Gg. Kutisari Selatan No. 397, Tomohon, Riau 26673','1981-07-04 00:00:00'),
	('user32','Gg. K.H. Wahid Hasyim No. 242, Kota Administrasi Jakarta Pusat, Sumatera Utara 58677','1972-06-22 00:00:00'),
	('user33','Gang Peta No. 98, Payakumbuh, SS 64600','1992-07-08 00:00:00'),
	('user34','Jl. Yos Sudarso No. 6, Purwokerto, Sulawesi Utara 87929','1966-01-05 00:00:00'),
	('user35','Gang Cikutra Timur No. 129, Sorong, JB 57274','1997-09-28 00:00:00'),
	('user36','Gg. Monginsidi No. 68, Lhokseumawe, JB 21530','1966-02-23 00:00:00'),
	('user37','Jl. HOS. Cokroaminoto No. 7, Salatiga, BB 45275','1967-03-22 00:00:00'),
	('user38','Jl. Rajawali Timur No. 4, Denpasar, AC 66316','1982-06-20 00:00:00'),
	('user39','Gang Ir. H. Djuanda No. 36, Kota Administrasi Jakarta Timur, YO 75547','1987-09-11 00:00:00'),
	('user40','Jalan Sadang Serang No. 721, Tegal, Maluku Utara 15245','1972-03-31 00:00:00'),
	('user41','Gang Rajawali Timur No. 03, Subulussalam, Kalimantan Barat 82731','1999-12-13 00:00:00'),
	('user42','Gg. Dipatiukur No. 77, Tarakan, JT 12169','1970-09-14 00:00:00'),
	('user43','Jl. Rajawali Barat No. 28, Tanjungpinang, KR 26422','1970-02-21 00:00:00'),
	('user44','Jalan Rumah Sakit No. 6, Palu, Bengkulu 52733','1968-09-30 00:00:00'),
	('user45','Jalan Siliwangi No. 152, Kendari, Maluku Utara 59784','1984-06-14 00:00:00'),
	('user46','Jalan S. Parman No. 1, Palembang, Kalimantan Barat 07888','2006-01-01 00:00:00'),
	('user47','Gang Moch. Ramdan No. 72, Ternate, SU 01802','1971-10-03 00:00:00'),
	('user48','Jalan Cikutra Timur No. 0, Tegal, Kalimantan Barat 68956','1978-08-03 00:00:00'),
	('user49','Jl. Cihampelas No. 0, Bukittinggi, KS 92544','1995-02-05 00:00:00'),
	('user50','Gang Pasteur No. 4, Prabumulih, NB 56403','1996-02-01 00:00:00');

INSERT INTO DOKTER_HEWAN VALUES ('user51','STR-398544'),
	('user52','STR-861108'),
	('user53','STR-574891'),
	('user54','STR-318154'),
	('user55','STR-561830'),
	('user56','STR-551222'),
	('user57','STR-663450'),
	('user58','STR-500877'),
	('user59','STR-856553'),
	('user60','STR-245418'),
	('user61','STR-411353'),
	('user62','STR-328615'),
	('user63','STR-883112'),
	('user64','STR-788001'),
	('user65','STR-732163');

INSERT INTO SPESIALISASI VALUES ('user51','Primata'),
	('user52','Mamalia Besar'),
	('user53','Unggas'),
	('user54','Reptil'),
	('user55','Satwa Liar'),
	('user56','Unggas'),
	('user57','Reptil'),
	('user58','Hewan Eksotik'),
	('user59','Hewan Eksotik'),
	('user60','Satwa Liar'),
	('user61','Mamalia Kecil'),
	('user62','Reptil'),
	('user63','Primata'),
	('user64','Amfibi'),
	('user65','Mamalia Besar'),
	('user51','Ikan'),
	('user52','Mamalia Kecil'),
	('user53','Satwa Liar'),
	('user54','Unggas'),
	('user55','Unggas'),
	('user56','Reptil'),
	('user57','Satwa Liar');

INSERT INTO PENJAGA_HEWAN VALUES ('user66','5ec1d005-6bf4-415a-94aa-8ef95bf8865e'),
	('user67','1948142c-6f39-41d4-a890-0577f55960f5'),
	('user68','f8ceff89-0f52-4531-b6f2-711513021c03'),
	('user69','859953ea-2737-4b51-b144-fdfcfbede7b2'),
	('user70','6361be4c-6bfa-462f-868e-7bdb8c33c1a0'),
	('user71','72030596-2197-4f4e-8b41-0fd021d6a88c'),
	('user72','8da11759-0a17-4497-ac7d-aa94cab5ea24'),
	('user73','97cbb22d-4493-4e82-a9ea-5e2b13168bf2'),
	('user74','c1e833b1-35a3-40bb-afb4-09cb0b32fc6c'),
	('user75','6572c5f3-ab55-42be-82c7-3c46283f5098');

INSERT INTO PELATIH_HEWAN VALUES ('user76','a96e7b5a-7093-4e6e-984e-da79f593122b'),
	('user77','1a727c76-7d36-4cc1-bbf1-13ba935055c5'),
	('user78','6b664850-47d5-4f15-86a9-0da3db10080a'),
	('user79','aa2648c9-3fc7-412e-8258-b63fcfebe116'),
	('user80','034dcf7d-188d-4934-b031-7f8ada462ef7'),
	('user81','c2af5ad4-e474-4b76-9979-9cb9c3b49535'),
	('user82','67a2e628-ebdc-46d2-b880-f9d83455f6d7'),
	('user83','86066bcd-ef59-40d5-a4e4-9a0d3fc9b9ef'),
	('user84','cd9bf963-4334-4bde-886d-8ebabd7b7288'),
	('user85','a9d53421-c47d-440f-91cf-70ff42610aa4');

INSERT INTO STAF_ADMIN VALUES ('user86','06c03c04-22dd-4e1c-afd7-217ab1461b6d'),
	('user87','62c9bd3d-118c-4e16-ad25-eb38c50af03d'),
	('user88','43e0e44b-a220-450e-88c6-2b6f6128b3a5'),
	('user89','bf4ec599-fcd7-4954-94e4-0a5b145978c5'),
	('user90','33952df7-b1db-4ed0-a734-486fa29a7d1a'),
	('user91','3c08915f-0e13-4777-8606-9115e1406102'),
	('user92','0f7b5beb-2594-466c-99f0-88e61ca6b5ca'),
	('user93','c7f17648-4c6e-4f62-997f-97d73e104634'),
	('user94','df4e1023-0e25-46b8-8b73-0080c011bbea'),
	('user95','7d98a71c-4828-430f-9ebb-7c085cf9b063');

INSERT INTO HABITAT VALUES ('Rawa',3526.99,153.0,'Suhu: 22°C, Kelembapan: 79%, Vegetasi: Pepohonan'),
	('Hutan Tropis',3986.18,55.0,'Suhu: 27°C, Kelembapan: 70%, Vegetasi: Pepohonan'),
	('Hutan',4167.56,171.0,'Suhu: 26°C, Kelembapan: 35%, Vegetasi: Pepohonan'),
	('Savanna',4635.06,172.0,'Suhu: 28°C, Kelembapan: 69%, Vegetasi: Rumput'),
	('Padang Rumput',2414.82,91.0,'Suhu: 31°C, Kelembapan: 78%, Vegetasi: Rumput'),
	('Pantai',4757.22,86.0,'Suhu: 37°C, Kelembapan: 57%, Vegetasi: Rumput'),
	('Gunung',3849.4,107.0,'Suhu: 35°C, Kelembapan: 56%, Vegetasi: Semak'),
	('Laut',3425.29,105.0,'Suhu: 30°C, Kelembapan: 36%, Vegetasi: Pepohonan');

INSERT INTO HEWAN VALUES ('a93ead3f-dbe9-4188-80ad-a1121e4484cf','Buster','Buaya','Australia','2021-04-18 00:00:00','Sehat','Rawa','https://example.com/photo66.jpg'),
	('28dbda86-6918-4fa1-bf92-026409e9ba41','Tommy','Iguana','Amerika','2001-07-22 00:00:00','Sakit','Hutan Tropis','https://example.com/photo299.jpg'),
	('7226d729-65d4-400b-8828-b97cd2fe7ec0','Gracie','Kucing','Eropa','2011-02-14 00:00:00','Sehat','Hutan','https://example.com/photo12.jpg'),
	('2181f896-37a5-4067-9014-b8e60cd29d5b','Chloe','Singa','Afrika','2013-10-15 00:00:00','Sehat','Savanna','https://example.com/photo792.jpg'),
	('f0ee074b-76be-4ad1-a1a9-2b6369cbf4dc','Max','Rubah Merah','Australia','2000-04-13 00:00:00','Sakit','Hutan','https://example.com/photo831.jpg'),
	('15e4f927-4f4b-4d9f-9442-baa159b427dd','Nala','Burung Hantu','Eropa','2023-02-22 00:00:00','Sehat','Hutan','https://example.com/photo986.jpg'),
	('d545902c-6b1c-4139-bd1b-228ec425f84e','Daisy','Anjing','Amerika','2003-08-12 00:00:00','Sehat','Padang Rumput','https://example.com/photo814.jpg'),
	('75884d4d-ef00-4f32-bdec-3548370bbe3f','Chloe','Penyu','Eropa','2014-04-24 00:00:00','Sehat','Pantai','https://example.com/photo448.jpg'),
	('6df036cd-a77c-4918-b48e-7c1bb03ed989','Jake','Harimau','Afrika','2007-04-04 00:00:00','Dalam pemantauan','Hutan Tropis','https://example.com/photo8.jpg'),
	('c4d0c53e-9ac8-4252-b014-1961a3e9ebd5','Ziggy','Dolphin','Afrika','2001-08-19 00:00:00','Sehat','Laut','https://example.com/photo550.jpg'),
	('b5f960d7-35f2-4f08-a2a4-6a9411fa052d','Jack','Kuda','Eropa','2008-03-02 00:00:00','Sehat','Padang Rumput','https://example.com/photo374.jpg'),
	('29ef4adb-2f3a-42bb-b5e4-f33039ffe86e','Tina','Rubah','Afrika','2001-09-29 00:00:00','Sehat','Hutan','https://example.com/photo678.jpg'),
	('6bfa0f97-98d6-4695-92b3-d1c3fd534c85','Pepper','Kuda Poni','Eropa','2006-10-27 00:00:00','Sehat','Padang Rumput','https://example.com/photo802.jpg'),
	('b555f602-6b7b-4f7e-abd7-1816746bff18','Tommy','Ikan Paus','Asia','2016-09-17 00:00:00','Sehat','Laut','https://example.com/photo251.jpg'),
	('a8953c8d-086a-4787-a312-71620357e001','Zara','Ikan Paus','Amerika','2016-04-01 00:00:00','Sakit','Laut','https://example.com/photo868.jpg'),
	('56546713-8b1e-41a0-b7d1-29aef53d6f63','Chloe','Ular','Afrika','2023-12-28 00:00:00','Sehat','Hutan','https://example.com/photo816.jpg'),
	('51ca4fda-c10f-4c32-bd66-cf7a7ae0e415','Leo','Orangutan','Asia','2013-07-29 00:00:00','Sehat','Hutan Tropis','https://example.com/photo912.jpg'),
	('5541e8a9-11e5-44d9-b1da-2681e88742f7','Cooper','Penyu','Eropa','2021-02-26 00:00:00','Sehat','Pantai','https://example.com/photo11.jpg'),
	('68be946f-f38d-4e05-a8e6-66c93a7dc9a1','Rexy','Penguin','Asia','2023-11-27 00:00:00','Sakit','Pantai','https://example.com/photo788.jpg'),
	('5f2e9a77-bd81-4c8f-ab58-8969e1a887b5','Sophie','Rubah','Afrika','2020-10-02 00:00:00','Sehat','Hutan','https://example.com/photo770.jpg'),
	('0eab43f2-ada6-4bb7-bdb5-402c22eb344f','Chloe','Anjing','Asia','2005-12-09 00:00:00','Sakit','Padang Rumput','https://example.com/photo409.jpg'),
	('3e05e38e-4ee0-44e2-941b-bd3db3e09ab4','Maggie','Ular','Afrika','2005-04-06 00:00:00','Sakit','Hutan','https://example.com/photo469.jpg'),
	('30a7d589-8456-4cc1-9e60-9de65ff88f84','Buster','Macan Tutul','Amerika','2015-09-13 00:00:00','Sehat','Hutan Tropis','https://example.com/photo654.jpg'),
	('7ecdfd61-4419-4cca-907e-4b8cf11ccf27','Oliver','Kanguru','Australia','2020-09-05 00:00:00','Sakit','Padang Rumput','https://example.com/photo694.jpg'),
	('1c4369bc-57d1-42ef-b975-379353873a81','Ziggy','Badak','Eropa','2001-03-11 00:00:00','Sehat','Savanna','https://example.com/photo466.jpg'),
	('cf8f1658-d3ee-431a-84a9-802079f2bb32','Rocky','Cheetah','Eropa','2002-02-09 00:00:00','Sakit','Savanna','https://example.com/photo460.jpg'),
	('5957504f-23f6-4f51-9a5f-ffcc3c20274b','Lucy','Orangutan','Eropa','2022-02-15 00:00:00','Sehat','Hutan Tropis','https://example.com/photo153.jpg'),
	('ccfc4ba8-a0e9-47e1-b734-431e7d6dc3a4','Lily','Rubah Merah','Eropa','2013-04-09 00:00:00','Sehat','Hutan','https://example.com/photo683.jpg'),
	('302ab435-288b-4db7-9b15-e3ccd65d036e','Bailey','Cheetah','Afrika','2000-07-21 00:00:00','Sehat','Savanna','https://example.com/photo55.jpg'),
	('c73cad48-3420-4ccd-be73-02bffe28d40f','Buddy','Kucing','Amerika','2015-04-19 00:00:00','Sehat','Hutan','https://example.com/photo143.jpg'),
	('d485123f-117c-493a-9df9-d002984f84bb','Shadow','Harimau','Asia','2001-04-05 00:00:00','Sehat','Hutan Tropis','https://example.com/photo731.jpg'),
	('efecbdde-3ab0-4d1a-b21f-a5b2a391da9a','Luna','Jaguar','Amerika','2000-04-01 00:00:00','Sehat','Hutan Tropis','https://example.com/photo113.jpg'),
	('751eaee1-0e09-408e-ae56-636d9d54269d','Bella','Gajah','Amerika','2018-09-03 00:00:00','Sehat','Savanna','https://example.com/photo437.jpg'),
	('9635be93-6e30-4d49-b31a-acd05d4f0073','Harley','Zebra','Afrika','2000-07-29 00:00:00','Sakit','Savanna','https://example.com/photo480.jpg'),
	('baa97802-8d00-4699-ad8b-bfd044b959d8','Daisy','Rubah','Eropa','2002-08-12 00:00:00','Sehat','Hutan','https://example.com/photo819.jpg'),
	('d9973c16-9684-4ce3-847f-a5db11b6b69f','Rex','Beruang','Eropa','2022-05-11 00:00:00','Sehat','Gunung','https://example.com/photo444.jpg'),
	('70ab0d25-2497-4cd0-9a4f-ecfdc592d460','Shadow','Koala','Australia','2010-07-28 00:00:00','Sehat','Hutan','https://example.com/photo261.jpg'),
	('4c86b545-db9a-4468-9394-7b776fa6e921','Oliver','Cheetah','Asia','2000-02-04 00:00:00','Sehat','Savanna','https://example.com/photo383.jpg'),
	('4295bf84-c84a-46b5-8243-0cc64e8eea3e','Lucy','Zebra','Amerika','2003-06-17 00:00:00','Sehat','Savanna','https://example.com/photo310.jpg'),
	('220ddce0-85ca-48ba-a9d3-d802c92e5ce1','Gracie','Kanguru','Afrika','2002-01-10 00:00:00','Sehat','Padang Rumput','https://example.com/photo469.jpg');

INSERT INTO CATATAN_MEDIS VALUES ('7ecdfd61-4419-4cca-907e-4b8cf11ccf27','user65','2025-03-29 00:00:00','Infeksi','Vaksinasi','Sakit','Observasi lanjutan'),
	('75884d4d-ef00-4f32-bdec-3548370bbe3f','user54','2025-04-20 00:00:00',NULL,NULL,'Sehat',NULL),
	('9635be93-6e30-4d49-b31a-acd05d4f0073','user52','2025-04-04 00:00:00','Radang','Obat B','Sakit','Kontrol dua minggu'),
	('6bfa0f97-98d6-4695-92b3-d1c3fd534c85','user52','2025-04-04 00:00:00',NULL,NULL,'Sehat',NULL),
	('5541e8a9-11e5-44d9-b1da-2681e88742f7','user54','2025-03-25 00:00:00',NULL,NULL,'Sehat',NULL),
	('cf8f1658-d3ee-431a-84a9-802079f2bb32','user60','2025-04-11 00:00:00','Fraktur','Obat B','Sakit','Kontrol seminggu'),
	('28dbda86-6918-4fa1-bf92-026409e9ba41','user57','2025-04-06 00:00:00','Radang','Obat A','Sakit','Kontrol dua minggu'),
	('4c86b545-db9a-4468-9394-7b776fa6e921','user53','2025-04-17 00:00:00',NULL,NULL,'Sehat',NULL),
	('a8953c8d-086a-4787-a312-71620357e001','user51','2025-04-03 00:00:00','Flu','Obat A','Sakit','Kontrol seminggu'),
	('6df036cd-a77c-4918-b48e-7c1bb03ed989','user60','2025-04-19 00:00:00','Radang','Vaksinasi','Dalam pemantauan','Observasi lanjutan');

INSERT INTO PAKAN VALUES ('6bfa0f97-98d6-4695-92b3-d1c3fd534c85','2025-04-26 18:49:13','Buah',1.0,'Menunggu pemberian'),
	('cf8f1658-d3ee-431a-84a9-802079f2bb32','2025-04-27 01:49:13','Pelet',2.0,'Menunggu pemberian'),
	('4c86b545-db9a-4468-9394-7b776fa6e921','2025-04-23 10:49:13','Sayuran',3.0,'Menunggu pemberian'),
	('30a7d589-8456-4cc1-9e60-9de65ff88f84','2025-04-25 04:49:13','Buah',4.0,'Selesai Diberikan'),
	('9635be93-6e30-4d49-b31a-acd05d4f0073','2025-04-28 12:49:13','Pelet',1.0,'Selesai Diberikan');
