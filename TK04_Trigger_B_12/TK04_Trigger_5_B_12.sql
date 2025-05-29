SET search_path TO SIZOPI;

-- =================================================================
-- 0. TABEL SNAPSHOT TOP-5
-- =================================================================
CREATE TABLE IF NOT EXISTS top5_adopter (
  rank           integer PRIMARY KEY,
  id_adopter     uuid       NOT NULL,
  nama_adopter   text       NOT NULL,
  total          bigint     NOT NULL,
  updated_at     timestamp with time zone NOT NULL DEFAULT now()
);

-- =================================================================
-- 1. TRIGGER: SINKRONISASI TOTAL_KONTRIBUSI DI TABEL ADOPTER
-- =================================================================
CREATE OR REPLACE FUNCTION sync_total_contrib()
RETURNS TRIGGER AS $$
DECLARE
  affected_adopter uuid;
  new_total        integer;
  adopter_name     text;
BEGIN
  IF (TG_OP = 'DELETE') THEN
    affected_adopter := OLD.id_adopter;
  ELSE
    affected_adopter := NEW.id_adopter;
  END IF;

  SELECT COALESCE(SUM(kontribusi_finansial),0)
    INTO new_total
  FROM adopsi
  WHERE id_adopter = affected_adopter
    AND status_pembayaran = 'lunas';

  UPDATE adopter
     SET total_kontribusi = new_total
   WHERE id_adopter = affected_adopter;

  SELECT
    COALESCE(i.nama, org.nama_organisasi)
    INTO adopter_name
  FROM adopter a
  LEFT JOIN individu i       ON a.id_adopter = i.id_adopter
  LEFT JOIN organisasi org   ON a.id_adopter = org.id_adopter
  WHERE a.id_adopter = affected_adopter;

  RAISE NOTICE
    'SUKSES: Total kontribusi adopter "%" telah diperbarui.',
    adopter_name;
  RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_sync_total_contrib ON adopsi;
CREATE TRIGGER trg_sync_total_contrib
    AFTER INSERT OR UPDATE OR DELETE
    ON adopsi
    FOR EACH ROW
    EXECUTE FUNCTION sync_total_contrib();

-- =================================================================
-- 2. TRIGGER: POPULATE TOP-5 KE snapshot DAN NOTIFY
-- =================================================================
SET search_path TO SIZOPI;

CREATE OR REPLACE FUNCTION notify_top5()
RETURNS TRIGGER AS $$
DECLARE
  first_name   text;
  first_amount bigint;
BEGIN
  TRUNCATE top5_adopter;

  WITH ranked AS (
    SELECT
      a.id_adopter,
      COALESCE(i.nama, org.nama_organisasi) AS nama_adopter,
      SUM(o.kontribusi_finansial)::bigint    AS total,
      ROW_NUMBER() OVER (
        ORDER BY SUM(o.kontribusi_finansial) DESC
      ) AS rk
    FROM adopsi o
    JOIN adopter a           USING(id_adopter)
    LEFT JOIN individu i     USING(id_adopter)
    LEFT JOIN organisasi org USING(id_adopter)
    WHERE o.status_pembayaran = 'lunas'
      AND (
           (o.tgl_mulai_adopsi   BETWEEN CURRENT_DATE - INTERVAL '1 year' AND CURRENT_DATE)
        OR (o.tgl_berhenti_adopsi BETWEEN CURRENT_DATE - INTERVAL '1 year' AND CURRENT_DATE)
      )
    GROUP BY 1,2
  )
  INSERT INTO top5_adopter(rank, id_adopter, nama_adopter, total)
  SELECT rk, id_adopter, nama_adopter, total
    FROM ranked
   WHERE rk <= 5;

  SELECT nama_adopter, total
    INTO first_name, first_amount
    FROM top5_adopter
   WHERE rank = 1;

  RAISE NOTICE
    'SUKSES: Daftar Top 5 Adopter satu tahun terakhir berhasil diperbarui, dengan peringkat pertama dengan nama adopter "%" berkontribusi sebesar "RP%".',
    first_name, first_amount;
  RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_notify_top5 ON adopsi;
CREATE TRIGGER trg_notify_top5
  AFTER INSERT OR UPDATE OR DELETE
  ON adopsi
  FOR EACH STATEMENT
  EXECUTE FUNCTION notify_top5();
