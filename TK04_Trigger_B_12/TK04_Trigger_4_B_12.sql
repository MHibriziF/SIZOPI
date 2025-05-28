SET search_path TO SIZOPI;

-- =================================================================
-- 1. TRIGGER: PEMERIKSAAN KAPASITAS ATRAKSI SAAT RESERVASI 
-- =================================================================
CREATE OR REPLACE FUNCTION cek_kapasitas_atraksi()
RETURNS TRIGGER AS $$
DECLARE
    total_terpesan INTEGER;
    kapasitas_max INTEGER;
    sisa INTEGER;
BEGIN
    SELECT f.kapasitas_max
    INTO kapasitas_max
    FROM FASILITAS f
    WHERE f.nama = NEW.nama_fasilitas;

    IF kapasitas_max IS NULL THEN
        RAISE EXCEPTION 'Fasilitas % tidak ditemukan.', NEW.nama_fasilitas;
    END IF;

    IF TG_OP = 'UPDATE' THEN
        SELECT COALESCE(SUM(jumlah_tiket), 0)
        INTO total_terpesan
        FROM RESERVASI
        WHERE nama_fasilitas = NEW.nama_fasilitas
          AND tanggal_kunjungan = NEW.tanggal_kunjungan
          AND status = 'Terjadwal'
          AND NOT (
              username_p = OLD.username_p AND
              nama_fasilitas = OLD.nama_fasilitas AND
              tanggal_kunjungan = OLD.tanggal_kunjungan
          );
    ELSE
        SELECT COALESCE(SUM(jumlah_tiket), 0)
        INTO total_terpesan
        FROM RESERVASI
        WHERE nama_fasilitas = NEW.nama_fasilitas
          AND tanggal_kunjungan = NEW.tanggal_kunjungan
          AND status = 'Terjadwal';
    END IF;

    sisa := kapasitas_max - total_terpesan;

    IF NEW.jumlah_tiket > sisa THEN
        RAISE EXCEPTION 'ERROR: Kapasitas tersisa "%" tiket, atraksi tidak mencukupi untuk sejumlah "%" tiket yang diminta.', sisa, NEW.jumlah_tiket;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trigger_cek_kapasitas_atraksi
BEFORE INSERT OR UPDATE ON RESERVASI
FOR EACH ROW
WHEN (NEW.status = 'Terjadwal')
EXECUTE FUNCTION cek_kapasitas_atraksi();
