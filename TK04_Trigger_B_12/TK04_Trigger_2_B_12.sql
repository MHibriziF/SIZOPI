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


DROP TRIGGER IF EXISTS trg_cek_duplikat_satwa ON HEWAN;

CREATE TRIGGER trg_cek_duplikat_satwa
BEFORE INSERT ON HEWAN
FOR EACH ROW
EXECUTE FUNCTION cek_duplikat_satwa();