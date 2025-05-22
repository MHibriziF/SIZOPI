SET search_path TO SIZOPI;

-- =================================================================
-- 1. TRIGGER: PEMERIKSAAN DUPLIKASI USERNAME SAAT REGISTRASI
-- =================================================================
CREATE OR REPLACE FUNCTION check_duplicate_username() 
RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM PENGGUNA WHERE username = NEW.username) THEN
        RAISE EXCEPTION 'ERROR: Username "%" sudah digunakan, silakan pilih username lain.', NEW.username;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trigger_check_duplicate_username
    BEFORE INSERT ON PENGGUNA
    FOR EACH ROW
    EXECUTE FUNCTION check_duplicate_username();

-- =================================================================
-- 2. STORED PROCEDURE: VERIFIKASI KREDENSIAL SAAT LOGIN
-- =================================================================

CREATE OR REPLACE FUNCTION verify_user_credentials(
    input_username VARCHAR(50),
    input_password VARCHAR(50)
) 
RETURNS TABLE(
    is_valid BOOLEAN,
    message TEXT,
    user_roles TEXT[]
) AS $$
DECLARE
    stored_password VARCHAR(50);
    roles TEXT[] := '{}';
BEGIN
    SELECT password INTO stored_password 
    FROM PENGGUNA 
    WHERE username = input_username;
    
    IF stored_password IS NULL THEN
        RETURN QUERY SELECT FALSE, 'Username atau password salah, silakan coba lagi.', roles;
        RETURN;
    END IF;
    
    IF stored_password != input_password THEN
        RETURN QUERY SELECT FALSE, 'Username atau password salah, silakan coba lagi.', roles;
        RETURN;
    END IF;
    
    IF EXISTS (SELECT 1 FROM PENGUNJUNG WHERE username_p = input_username) THEN
        roles := array_append(roles, 'pengunjung');
    END IF;
    
    IF EXISTS (SELECT 1 FROM DOKTER_HEWAN WHERE username_DH = input_username) THEN
        roles := array_append(roles, 'dokter');
    END IF;
    
    IF EXISTS (SELECT 1 FROM PENJAGA_HEWAN WHERE username_jh = input_username) THEN
        roles := array_append(roles, 'penjaga');
    END IF;

    IF EXISTS (SELECT 1 FROM PELATIH_HEWAN WHERE username_lh = input_username) THEN
        roles := array_append(roles, 'pelatih');
    END IF;
    
    IF EXISTS (SELECT 1 FROM STAF_ADMIN WHERE username_sa = input_username) THEN
        roles := array_append(roles, 'admin');
    END IF;
    
    RETURN QUERY SELECT TRUE, 'Login berhasil.', roles;
END;
$$ LANGUAGE plpgsql;

-- =================================================================
-- 3. FUNCTION HELPER: REGISTRASI USER DENGAN VALIDASI
-- =================================================================
CREATE OR REPLACE FUNCTION register_new_user(
    p_username VARCHAR(50),
    p_email VARCHAR(100),
    p_password VARCHAR(50),
    p_nama_depan VARCHAR(50),
    p_nama_tengah VARCHAR(50),
    p_nama_belakang VARCHAR(50),
    p_no_telepon VARCHAR(15),
    p_role VARCHAR(20),
    p_role_data JSONB DEFAULT '{}'::jsonb
)
RETURNS TABLE(
    success BOOLEAN,
    message TEXT
) AS $$
DECLARE
    new_id_staf UUID;
BEGIN
    IF EXISTS (SELECT 1 FROM PENGGUNA WHERE email = p_email) THEN
        RETURN QUERY SELECT FALSE, 'ERROR: Email sudah digunakan, silakan gunakan email lain.';
        RETURN;
    END IF;
    BEGIN
        INSERT INTO PENGGUNA (username, email, password, nama_depan, nama_tengah, nama_belakang, no_telepon)
        VALUES (p_username, p_email, p_password, p_nama_depan, p_nama_tengah, p_nama_belakang, p_no_telepon);
    EXCEPTION 
        WHEN OTHERS THEN
            RETURN QUERY SELECT FALSE, SQLERRM;
            RETURN;
    END;
    
    CASE p_role
        WHEN 'pengunjung' THEN
            INSERT INTO PENGUNJUNG (username_p, alamat, tgl_lahir)
            VALUES (p_username, 
                    (p_role_data->>'alamat')::VARCHAR(200), 
                    (p_role_data->>'tgl_lahir')::DATE);
                    
        WHEN 'dokter' THEN
            INSERT INTO DOKTER_HEWAN (username_DH, no_STR)
            VALUES (p_username, (p_role_data->>'no_str')::VARCHAR(50));
            
            IF p_role_data ? 'spesialisasi' THEN
                INSERT INTO SPESIALISASI (username_SH, nama_spesialis)
                SELECT p_username, jsonb_array_elements_text(p_role_data->'spesialisasi');
            END IF;
            
        WHEN 'penjaga' THEN
            new_id_staf := uuid_generate_v4();
            INSERT INTO PENJAGA_HEWAN (username_jh, id_staf)
            VALUES (p_username, new_id_staf);
            
        WHEN 'pelatih' THEN
            new_id_staf := uuid_generate_v4();
            INSERT INTO PELATIH_HEWAN (username_lh, id_staf)
            VALUES (p_username, new_id_staf);
            
        WHEN 'admin' THEN
            new_id_staf := uuid_generate_v4();
            INSERT INTO STAF_ADMIN (username_sa, id_staf)
            VALUES (p_username, new_id_staf);
            
        ELSE
            DELETE FROM PENGGUNA WHERE username = p_username;
            RETURN QUERY SELECT FALSE, 'ERROR: Role tidak valid.';
            RETURN;
    END CASE;
    
    RETURN QUERY SELECT TRUE, 'Registrasi berhasil! Silakan login.';
    
EXCEPTION 
    WHEN OTHERS THEN
        DELETE FROM PENGGUNA WHERE username = p_username;
        RETURN QUERY SELECT FALSE, 'ERROR: ' || SQLERRM;
END;
$$ LANGUAGE plpgsql;

-- =================================================================
-- 4. TRIGGER TAMBAHAN: VALIDASI EMAIL FORMAT
-- =================================================================
CREATE OR REPLACE FUNCTION validate_email_format() 
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.email !~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$' THEN
        RAISE EXCEPTION 'ERROR: Format email tidak valid. Silakan masukkan email yang benar.';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trigger_validate_email
    BEFORE INSERT OR UPDATE ON PENGGUNA
    FOR EACH ROW
    EXECUTE FUNCTION validate_email_format();

-- =================================================================
-- 5. FUNCTION UNTUK MENDAPATKAN INFORMASI USER
-- =================================================================

CREATE OR REPLACE FUNCTION get_user_info(p_username VARCHAR(50))
RETURNS TABLE(
    username VARCHAR(50),
    email VARCHAR(100),
    nama_depan VARCHAR(50),
    nama_tengah VARCHAR(50),
    nama_belakang VARCHAR(50),
    no_telepon VARCHAR(15),
    user_role VARCHAR(20),
    role_data JSONB
) AS $$
DECLARE
    role_info JSONB := '{}'::jsonb;
    user_role VARCHAR(20);
BEGIN
    IF EXISTS (SELECT 1 FROM PENGUNJUNG WHERE username_p = p_username) THEN
        user_role := 'pengunjung';
        SELECT jsonb_build_object(
            'alamat', alamat,
            'tgl_lahir', tgl_lahir
        ) INTO role_info
        FROM PENGUNJUNG WHERE username_p = p_username;
        
    ELSIF EXISTS (SELECT 1 FROM DOKTER_HEWAN WHERE username_DH = p_username) THEN
        user_role := 'dokter';
        SELECT jsonb_build_object(
            'no_STR', dh.no_STR,
            'spesialisasi', COALESCE(array_agg(s.nama_spesialis), ARRAY[]::VARCHAR[])
        ) INTO role_info
        FROM DOKTER_HEWAN dh
        LEFT JOIN SPESIALISASI s ON dh.username_DH = s.username_SH
        WHERE dh.username_DH = p_username
        GROUP BY dh.no_STR;
        
    ELSIF EXISTS (SELECT 1 FROM PENJAGA_HEWAN WHERE username_jh = p_username) THEN
        user_role := 'penjaga';
        SELECT jsonb_build_object('id_staf', id_staf) INTO role_info
        FROM PENJAGA_HEWAN WHERE username_jh = p_username;
        
    ELSIF EXISTS (SELECT 1 FROM PELATIH_HEWAN WHERE username_lh = p_username) THEN
        user_role := 'pelatih';
        SELECT jsonb_build_object('id_staf', id_staf) INTO role_info
        FROM PELATIH_HEWAN WHERE username_lh = p_username;
        
    ELSIF EXISTS (SELECT 1 FROM STAF_ADMIN WHERE username_sa = p_username) THEN
        user_role := 'admin';
        SELECT jsonb_build_object('id_staf', id_staf) INTO role_info
        FROM STAF_ADMIN WHERE username_sa = p_username;
    END IF;
    
    RETURN QUERY 
    SELECT p.username, p.email, p.nama_depan, p.nama_tengah, p.nama_belakang, 
           p.no_telepon, user_role, role_info
    FROM PENGGUNA p 
    WHERE p.username = p_username;
END;
$$ LANGUAGE plpgsql;
