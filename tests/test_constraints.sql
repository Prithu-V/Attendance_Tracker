-- Phase 0: four constraint tests. Run with: psql "$DATABASE_URL" -f tests/test_constraints.sql
-- Each block must FAIL to insert; the script raises if a bad row is accepted.
BEGIN;

DO $$ BEGIN  -- 1. duplicate roll number
  INSERT INTO student (name, roll_no) VALUES ('Dup', 'CS001');
  RAISE EXCEPTION 'TEST 1 FAILED: duplicate roll_no accepted';
EXCEPTION WHEN unique_violation THEN RAISE NOTICE 'test 1 ok: duplicate roll_no rejected'; END $$;

DO $$ BEGIN  -- 2. end_time must be after start_time
  INSERT INTO sessions (session_name, start_time, end_time, token)
  VALUES ('Bad', now(), now() - interval '1 hour', 'badtime');
  RAISE EXCEPTION 'TEST 2 FAILED: end before start accepted';
EXCEPTION WHEN check_violation THEN RAISE NOTICE 'test 2 ok: end<=start rejected'; END $$;

DO $$ BEGIN  -- 3. duplicate token
  INSERT INTO sessions (session_name, start_time, end_time, token)
  VALUES ('Dup', now(), now() + interval '1 hour', 'seedopen');
  RAISE EXCEPTION 'TEST 3 FAILED: duplicate token accepted';
EXCEPTION WHEN unique_violation THEN RAISE NOTICE 'test 3 ok: duplicate token rejected'; END $$;

DO $$ BEGIN  -- 4. same student twice in one session
  INSERT INTO attendance (student_id, session_id)
  SELECT student_id, session_id FROM attendance LIMIT 1;
  RAISE EXCEPTION 'TEST 4 FAILED: duplicate attendance accepted';
EXCEPTION WHEN unique_violation THEN RAISE NOTICE 'test 4 ok: duplicate attendance rejected'; END $$;

ROLLBACK;
