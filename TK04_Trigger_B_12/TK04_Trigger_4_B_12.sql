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

-- =================================================================
-- 2. STORED PROCEDURE: PEMERIKSAAN KAPASITAS ATRAKSI SAAT RESERVASI 
-- =================================================================
CREATE OR REPLACE FUNCTION rotasi_oto_pelatih_func(atraksi VARCHAR)
RETURNS TEXT
LANGUAGE plpgsql AS $$
DECLARE
    pelatih_lama_row RECORD;
    pelatih_baru VARCHAR(50);
    jadwal_fasilitas TIMESTAMP;
    tgl_penugasan_baru TIMESTAMP;
    pesan TEXT := '';
    pelatih_sudah_dipakai TEXT[] := ARRAY[]::TEXT[];
BEGIN
    SELECT jadwal INTO jadwal_fasilitas FROM FASILITAS WHERE nama = atraksi;
    tgl_penugasan_baru := CURRENT_DATE + (jadwal_fasilitas - DATE_TRUNC('day', jadwal_fasilitas));

    FOR pelatih_lama_row IN
        SELECT username_lh
        FROM JADWAL_PENUGASAN
        WHERE nama_atraksi = atraksi
        GROUP BY username_lh
        HAVING MAX(tgl_penugasan) <= CURRENT_DATE - INTERVAL '3 months'
    LOOP
        pelatih_sudah_dipakai := array_append(pelatih_sudah_dipakai, pelatih_lama_row.username_lh);

        SELECT username_lh INTO pelatih_baru
        FROM PELATIH_HEWAN
        WHERE username_lh NOT IN (
            SELECT username_lh FROM JADWAL_PENUGASAN 
            WHERE nama_atraksi = atraksi OR tgl_penugasan = tgl_penugasan_baru
        )
        AND username_lh <> pelatih_lama_row.username_lh
        AND username_lh <> ALL(pelatih_sudah_dipakai)
        LIMIT 1;

        IF pelatih_baru IS NOT NULL THEN
            UPDATE JADWAL_PENUGASAN
            SET username_lh = pelatih_baru,
                tgl_penugasan = tgl_penugasan_baru
            WHERE username_lh = pelatih_lama_row.username_lh
              AND nama_atraksi = atraksi
              AND tgl_penugasan = (
                SELECT MAX(tgl_penugasan) FROM JADWAL_PENUGASAN
                WHERE username_lh = pelatih_lama_row.username_lh AND nama_atraksi = atraksi
              );

            pesan := pesan || format('SUKSES: Pelatih "%s" telah bertugas lebih dari 3 bulan di atraksi "%s" dan akan diganti.%s',
                pelatih_lama_row.username_lh, atraksi, E'\n');

            pelatih_sudah_dipakai := array_append(pelatih_sudah_dipakai, pelatih_baru);
        END IF;
    END LOOP;

    RETURN pesan;
END;
$$;
