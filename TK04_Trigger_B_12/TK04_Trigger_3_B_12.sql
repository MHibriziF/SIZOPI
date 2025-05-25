SET search_path TO SIZOPI;

-- =================================================================
-- 1. TRIGGER: SINKRONISASI REKAM MEDIS DAN JADWAL PEMERIKSAAN
-- =================================================================
CREATE OR REPLACE FUNCTION sync_medical_record_schedule() 
RETURNS TRIGGER AS $$
DECLARE
    hewan_nama VARCHAR(100);
    jadwal_terdekat DATE;
    jadwal_baru DATE;
    message_text TEXT;
BEGIN
    SELECT nama INTO hewan_nama 
    FROM HEWAN 
    WHERE id = NEW.id_hewan;
    
    IF NEW.status_kesehatan = 'Sakit' THEN
        jadwal_baru := NEW.tanggal_pemeriksaan + INTERVAL '7 days';
        
        SELECT MIN(tgl_pemeriksaan_selanjutnya) INTO jadwal_terdekat
        FROM JADWAL_PEMERIKSAAN_KESEHATAN
        WHERE id_hewan = NEW.id_hewan 
          AND tgl_pemeriksaan_selanjutnya >= NEW.tanggal_pemeriksaan;
        
        IF jadwal_terdekat IS NOT NULL THEN
            UPDATE JADWAL_PEMERIKSAAN_KESEHATAN
            SET tgl_pemeriksaan_selanjutnya = jadwal_baru
            WHERE id_hewan = NEW.id_hewan 
              AND tgl_pemeriksaan_selanjutnya = jadwal_terdekat;
              
            message_text := 'SUKSES: Jadwal pemeriksaan hewan "' || hewan_nama || '" telah diperbarui karena status kesehatan "Sakit".';
        ELSE
            INSERT INTO JADWAL_PEMERIKSAAN_KESEHATAN (id_hewan, tgl_pemeriksaan_selanjutnya, freq_pemeriksaan_rutin)
            VALUES (NEW.id_hewan, jadwal_baru, 
                    COALESCE((SELECT freq_pemeriksaan_rutin 
                             FROM JADWAL_PEMERIKSAAN_KESEHATAN 
                             WHERE id_hewan = NEW.id_hewan 
                             LIMIT 1), 3));
                             
            message_text := 'SUKSES: Jadwal pemeriksaan hewan "' || hewan_nama || '" telah diperbarui karena status kesehatan "Sakit".';
        END IF;
        
        RAISE NOTICE '%', message_text;

        UPDATE HEWAN 
        SET status_kesehatan = NEW.status_kesehatan 
        WHERE id = NEW.id_hewan;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trigger_sync_medical_record
    AFTER INSERT ON CATATAN_MEDIS
    FOR EACH ROW
    EXECUTE FUNCTION sync_medical_record_schedule();

-- =================================================================
-- 2. TRIGGER: PENAMBAHAN JADWAL PEMERIKSAAN SESUAI FREKUENSI
-- =================================================================
CREATE OR REPLACE FUNCTION add_periodic_medical_schedule() 
RETURNS TRIGGER AS $$
DECLARE
    hewan_nama VARCHAR(100);
    schedule_date DATE;  
    next_schedule_date DATE;
    year_end DATE;
    freq_months INT;
    message_text TEXT;
BEGIN
    SELECT nama INTO hewan_nama 
    FROM HEWAN 
    WHERE id = NEW.id_hewan;
    
    freq_months := NEW.freq_pemeriksaan_rutin;
    
    schedule_date := NEW.tgl_pemeriksaan_selanjutnya;  
    year_end := DATE_TRUNC('year', schedule_date) + INTERVAL '1 year' - INTERVAL '1 day';
    
    LOOP
        next_schedule_date := schedule_date + (freq_months || ' months')::INTERVAL;
        
        EXIT WHEN next_schedule_date > year_end;
        
        INSERT INTO JADWAL_PEMERIKSAAN_KESEHATAN (id_hewan, tgl_pemeriksaan_selanjutnya, freq_pemeriksaan_rutin)
        SELECT NEW.id_hewan, next_schedule_date, freq_months
        WHERE NOT EXISTS (
            SELECT 1 FROM JADWAL_PEMERIKSAAN_KESEHATAN 
            WHERE id_hewan = NEW.id_hewan 
              AND tgl_pemeriksaan_selanjutnya = next_schedule_date
        );
        
        schedule_date := next_schedule_date;  
    END LOOP;
    
    message_text := 'SUKSES: Jadwal pemeriksaan rutin hewan "' || hewan_nama || '" telah ditambahkan sesuai frekuensi.';
    RAISE NOTICE '%', message_text;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trigger_add_periodic_schedule
    AFTER INSERT ON JADWAL_PEMERIKSAAN_KESEHATAN
    FOR EACH ROW
    EXECUTE FUNCTION add_periodic_medical_schedule();

-- =================================================================
-- 3. STORED PROCEDURE: TAMBAH REKAM MEDIS DENGAN SINKRONISASI
-- =================================================================
CREATE OR REPLACE FUNCTION add_medical_record(
    p_id_hewan UUID,
    p_username_dh VARCHAR(50),
    p_tanggal_pemeriksaan DATE,
    p_diagnosis VARCHAR(100),
    p_pengobatan VARCHAR(100),
    p_status_kesehatan VARCHAR(50),
    p_catatan_tindak_lanjut VARCHAR(100) DEFAULT NULL
)
RETURNS TABLE(
    success BOOLEAN,
    message TEXT
) AS $$
DECLARE
    hewan_nama VARCHAR(100);
    jadwal_message TEXT := '';
BEGIN
    SELECT nama INTO hewan_nama FROM HEWAN WHERE id = p_id_hewan;
    IF hewan_nama IS NULL THEN
        RETURN QUERY SELECT FALSE, 'ERROR: Hewan tidak ditemukan.';
        RETURN;
    END IF;
    
    IF EXISTS (SELECT 1 FROM CATATAN_MEDIS 
               WHERE id_hewan = p_id_hewan 
                 AND tanggal_pemeriksaan = p_tanggal_pemeriksaan) THEN
        RETURN QUERY SELECT FALSE, 'ERROR: Rekam medis untuk tanggal ini sudah ada.';
        RETURN;
    END IF;
    
    IF p_status_kesehatan = 'Sakit' AND (p_diagnosis IS NULL OR p_pengobatan IS NULL) THEN
        RETURN QUERY SELECT FALSE, 'ERROR: Diagnosis dan pengobatan harus diisi untuk status sakit.';
        RETURN;
    END IF;
    
    INSERT INTO CATATAN_MEDIS (
        id_hewan, username_dh, tanggal_pemeriksaan, 
        diagnosis, pengobatan, status_kesehatan, catatan_tindak_lanjut
    ) VALUES (
        p_id_hewan, p_username_dh, p_tanggal_pemeriksaan,
        p_diagnosis, p_pengobatan, p_status_kesehatan, p_catatan_tindak_lanjut
    );
    
    IF p_status_kesehatan = 'Sakit' THEN
        jadwal_message := ' Jadwal pemeriksaan telah diperbarui karena status kesehatan "Sakit".';
    END IF;
    
    RETURN QUERY SELECT TRUE, 'SUKSES: Rekam medis hewan "' || hewan_nama || '" berhasil ditambahkan.' || jadwal_message;
    
EXCEPTION 
    WHEN OTHERS THEN
        RETURN QUERY SELECT FALSE, 'ERROR: ' || SQLERRM;
END;
$$ LANGUAGE plpgsql;

-- =================================================================
-- 4. STORED PROCEDURE: TAMBAH JADWAL PEMERIKSAAN DENGAN FREKUENSI
-- =================================================================
CREATE OR REPLACE FUNCTION add_medical_schedule(
    p_id_hewan UUID,
    p_tanggal_pemeriksaan DATE,
    p_frekuensi_bulan INT DEFAULT 3
)
RETURNS TABLE(
    success BOOLEAN,
    message TEXT
) AS $$
DECLARE
    hewan_nama VARCHAR(100);
BEGIN
    SELECT nama INTO hewan_nama FROM HEWAN WHERE id = p_id_hewan;
    IF hewan_nama IS NULL THEN
        RETURN QUERY SELECT FALSE, 'ERROR: Hewan tidak ditemukan.';
        RETURN;
    END IF;
    
    IF EXISTS (SELECT 1 FROM JADWAL_PEMERIKSAAN_KESEHATAN 
               WHERE id_hewan = p_id_hewan 
                 AND tgl_pemeriksaan_selanjutnya = p_tanggal_pemeriksaan) THEN
        RETURN QUERY SELECT FALSE, 'ERROR: Jadwal pemeriksaan untuk tanggal ini sudah ada.';
        RETURN;
    END IF;
    
    INSERT INTO JADWAL_PEMERIKSAAN_KESEHATAN (
        id_hewan, tgl_pemeriksaan_selanjutnya, freq_pemeriksaan_rutin
    ) VALUES (
        p_id_hewan, p_tanggal_pemeriksaan, p_frekuensi_bulan
    );
    
    RETURN QUERY SELECT TRUE, 'SUKSES: Jadwal pemeriksaan rutin hewan "' || hewan_nama || '" telah ditambahkan sesuai frekuensi.';
    
EXCEPTION 
    WHEN OTHERS THEN
        RETURN QUERY SELECT FALSE, 'ERROR: ' || SQLERRM;
END;
$$ LANGUAGE plpgsql;

-- =================================================================
-- 5. FUNCTION HELPER: MENDAPATKAN JADWAL PEMERIKSAAN HEWAN
-- =================================================================
CREATE OR REPLACE FUNCTION get_medical_schedules(p_id_hewan UUID)
RETURNS TABLE(
    id_hewan UUID,
    nama_hewan VARCHAR(100),
    tanggal_pemeriksaan DATE,
    frekuensi_bulan INT,
    days_until_checkup INT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        h.id,
        h.nama,
        j.tgl_pemeriksaan_selanjutnya,
        j.freq_pemeriksaan_rutin,
        (j.tgl_pemeriksaan_selanjutnya - CURRENT_DATE)::INT as days_until
    FROM HEWAN h
    JOIN JADWAL_PEMERIKSAAN_KESEHATAN j ON h.id = j.id_hewan
    WHERE h.id = p_id_hewan
    ORDER BY j.tgl_pemeriksaan_selanjutnya;
END;
$$ LANGUAGE plpgsql;

-- =================================================================
-- 6. FUNCTION HELPER: MENDAPATKAN REKAM MEDIS HEWAN
-- =================================================================
CREATE OR REPLACE FUNCTION get_medical_records(p_id_hewan UUID)
RETURNS TABLE(
    id_hewan UUID,
    nama_hewan VARCHAR(100),
    tanggal_pemeriksaan DATE,
    nama_dokter TEXT,
    status_kesehatan VARCHAR(50),
    diagnosis VARCHAR(100),
    pengobatan VARCHAR(100),
    catatan_tindak_lanjut VARCHAR(100)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        h.id,
        h.nama,
        cm.tanggal_pemeriksaan,
        (p.nama_depan || ' ' || p.nama_belakang)::TEXT,
        cm.status_kesehatan,
        cm.diagnosis,
        cm.pengobatan,
        cm.catatan_tindak_lanjut
    FROM HEWAN h
    JOIN CATATAN_MEDIS cm ON h.id = cm.id_hewan
    JOIN PENGGUNA p ON cm.username_dh = p.username
    WHERE h.id = p_id_hewan
    ORDER BY cm.tanggal_pemeriksaan DESC;
END;
$$ LANGUAGE plpgsql;

-- =================================================================
-- 7. TRIGGER TAMBAHAN: VALIDASI TANGGAL PEMERIKSAAN
-- =================================================================
CREATE OR REPLACE FUNCTION validate_medical_schedule_date() 
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.tgl_pemeriksaan_selanjutnya < CURRENT_DATE THEN
        RAISE EXCEPTION 'ERROR: Tanggal pemeriksaan tidak boleh di masa lalu.';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trigger_validate_schedule_date
    BEFORE INSERT OR UPDATE ON JADWAL_PEMERIKSAAN_KESEHATAN
    FOR EACH ROW
    EXECUTE FUNCTION validate_medical_schedule_date();