-- Ward population & SC share: SEC Delhi, Delimitation 2022 (draft) Annexure-1
-- "Wards Summary of Population" (2011 Census figures). ward_no refers to that
-- order's ward numbers. colony_profile is an approximate planning-status
-- characterization used as an infrastructure-deficit proxy; labeled approx.
-- SANGAM_VIHAR aggregates wards 163+168+169 (Sangam Vihar A+B+C).
-- AMBEDKAR_NGR mapped to ward 164 Dakshin Puri (resettlement belt of the
-- Ambedkar Nagar area).
UPDATE wards AS w SET
  population  = v.pop,
  sc_st_share = v.sc_share,
  indicators  = jsonb_build_object(
      'ward_no', v.ward_no,
      'sc_population', v.sc_pop,
      'colony_profile', v.profile,
      'source', 'SEC Delhi Delimitation 2022 Annexure-1 (Census 2011)'
  )
FROM (VALUES
  ('GOVIND_PURI',   74651, 10571, 0.1416, '176',         'unauthorized-regularized clusters, high density (approx.)'),
  ('KALKAJI',       44112,  2954, 0.0670, '175',         'planned colony with JJ pockets (approx.)'),
  ('SRINIWASPURI',  71374,  8231, 0.1153, '174',         'mixed planned/urban-village (approx.)'),
  ('CR_PARK',       62681,  3204, 0.0511, '171',         'planned colony (approx.)'),
  ('TUGHLAKABAD_X', 54978,  4830, 0.0879, '170',         'unauthorized-regularized extension (approx.)'),
  ('TUGHLAKABAD',   62786,  8940, 0.1424, '178',         'urban village + unauthorized clusters (approx.)'),
  ('SANGAM_VIHAR', 252632, 32300, 0.1279, '163+168+169', 'largest unauthorized-colony belt in Delhi (approx.)'),
  ('AMBEDKAR_NGR',  72967, 25724, 0.3525, '164',         'resettlement colony belt (approx.)'),
  ('MADANGIR',      52695, 23458, 0.4452, '165',         'resettlement colony (approx.)'),
  ('KHANPUR',       64453,  9414, 0.1461, '167',         'dense mixed/unauthorized (approx.)'),
  ('DEOLI',         55131,  9156, 0.1661, '161',         'urban village + unauthorized (approx.)'),
  ('BADARPUR',      69273, 20577, 0.2971, '180',         'urban village + unauthorized, industrial edge (approx.)')
) AS v(code, pop, sc_pop, sc_share, ward_no, profile)
WHERE w.ward_code = v.code;
