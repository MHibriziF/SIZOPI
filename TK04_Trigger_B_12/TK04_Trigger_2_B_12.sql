-- =================================================================
-- 1. TRIGGER: PEMERIKSAAN PERUBAHAN HEWAN
-- =================================================================
CREATE OR REPLACE FUNCTION log_perubahan_hewan()
RETURNS TRIGGER AS $$
BEGIN
    -- Cek dan log perubahan status_kesehatan (hanya jika berubah)
    IF NEW.status_kesehatan IS DISTINCT FROM OLD.status_kesehatan THEN
        INSERT INTO RIWAYAT_SATWA (satwa_id, kolom_perubahan, nilai_sebelum, nilai_sesudah)
        VALUES (NEW.id, 'STATUS_KESEHATAN', COALESCE(OLD.status_kesehatan, ''), COALESCE(NEW.status_kesehatan, ''));
        RAISE NOTICE 'SUKSES: Riwayat perubahan status kesehatan dari "%s" menjadi "%s" telah dicatat.',
            OLD.status_kesehatan, NEW.status_kesehatan;
    END IF;

    -- Selalu log perubahan habitat, meskipun nilainya sama
    INSERT INTO RIWAYAT_SATWA (satwa_id, kolom_perubahan, nilai_sebelum, nilai_sesudah)
    VALUES (NEW.id, 'NAMA_HABITAT', COALESCE(OLD.nama_habitat, ''), COALESCE(NEW.nama_habitat, ''));
    RAISE NOTICE 'SUKSES: Riwayat perubahan habitat dari "%s" menjadi "%s" telah dicatat.',
        OLD.nama_habitat, NEW.nama_habitat;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_log_perubahan_hewan ON HEWAN;

CREATE TRIGGER trg_log_perubahan_hewan
AFTER UPDATE ON HEWAN
FOR EACH ROW
EXECUTE PROCEDURE log_perubahan_hewan();

-- =================================================================
-- 2. TRIGGER: PEMERIKSAAN DUPLIKAT DATA SATWA
-- =================================================================
CREATE OR REPLACE FUNCTION cek_duplikat_satwa()
RETURNS TRIGGER AS $$
DECLARE
    sudah_ada INTEGER;
BEGIN
    SELECT COUNT(*) INTO sudah_ada
    FROM HEWAN
    WHERE nama = NEW.nama
      AND spesies = NEW.spesies
      AND asal_hewan = NEW.asal_hewan;

    IF sudah_ada > 0 THEN
        RAISE EXCEPTION
        'Data satwa atas nama "%", spesies "%", dan berasal dari "%" sudah terdaftar.',
        NEW.nama, NEW.spesies, NEW.asal_hewan;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =================================================================
-- 3. TRIGGER: PEMERIKSAAN KAPASITAS HABITAT
-- =================================================================

DROP TRIGGER IF EXISTS trg_cek_duplikat_satwa ON HEWAN;

CREATE TRIGGER trg_cek_duplikat_satwa
BEFORE INSERT ON HEWAN
FOR EACH ROW
EXECUTE FUNCTION cek_duplikat_satwa();

CREATE OR REPLACE FUNCTION cek_kapasitas_habitat()
RETURNS TRIGGER AS $$
DECLARE
    jumlah_hewan INTEGER;
    kapasitas_habitat INTEGER;
BEGIN
    -- Hitung jumlah hewan yang sudah ada di habitat tujuan
    SELECT COUNT(*) INTO jumlah_hewan
    FROM HEWAN
    WHERE nama_habitat = NEW.nama_habitat
      AND id IS DISTINCT FROM COALESCE(OLD.id, '00000000-0000-0000-0000-000000000000');

    -- Ambil kapasitas maksimum habitat
    SELECT kapasitas INTO kapasitas_habitat
    FROM HABITAT
    WHERE nama = NEW.nama_habitat;

    -- Jika jumlah hewan >= kapasitas, tolak INSERT/UPDATE
    IF jumlah_hewan >= kapasitas_habitat THEN
        RAISE EXCEPTION
            'Habitat "%" sudah penuh. Tidak dapat menambahkan hewan baru ke habitat ini.',
            NEW.nama_habitat;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_cek_kapasitas_habitat ON HEWAN;

CREATE TRIGGER trg_cek_kapasitas_habitat
BEFORE INSERT OR UPDATE ON HEWAN
FOR EACH ROW
EXECUTE FUNCTION cek_kapasitas_habitat();
