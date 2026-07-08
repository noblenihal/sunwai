-- Pilot geography: South Delhi PC, Kalkaji belt (AC-51 and neighbours).
-- lat/lon are APPROXIMATE locality centroids for the demo map; population
-- and indicators arrive with the F4 public-data loader (Census/UDISE).
INSERT INTO wards (ward_code, name, aliases, lat, lon) VALUES
('GOVIND_PURI',   'Govind Puri',            '{"govindpuri","govind puri ext","गोविंदपुरी"}', 28.5355, 77.2649),
('KALKAJI',       'Kalkaji',                '{"kalkaji extension","कालकाजी"}',               28.5494, 77.2591),
('CR_PARK',       'Chittaranjan Park',      '{"cr park","सी आर पार्क"}',                     28.5384, 77.2486),
('TUGHLAKABAD_X', 'Tughlakabad Extension',  '{"tughlakabad ext","तुगलकाबाद एक्सटेंशन"}',      28.5227, 77.2711),
('TUGHLAKABAD',   'Tughlakabad',            '{"tughlaqabad","तुगलकाबाद"}',                   28.5063, 77.2793),
('SANGAM_VIHAR',  'Sangam Vihar',           '{"संगम विहार"}',                                28.5030, 77.2390),
('AMBEDKAR_NGR',  'Ambedkar Nagar',         '{"अंबेडकर नगर"}',                               28.5175, 77.2345),
('BADARPUR',      'Badarpur',               '{"बदरपुर"}',                                    28.4930, 77.3020),
('DEOLI',         'Deoli',                  '{"देवली"}',                                     28.5115, 77.2330),
('KHANPUR',       'Khanpur',                '{"खानपुर"}',                                    28.5090, 77.2270),
('MADANGIR',      'Madangir',               '{"मदनगीर"}',                                    28.5150, 77.2210),
('SRINIWASPURI',  'Sriniwaspuri',           '{"srinivaspuri","श्रीनिवासपुरी"}',              28.5605, 77.2559)
ON CONFLICT (ward_code) DO UPDATE
SET name = EXCLUDED.name, aliases = EXCLUDED.aliases,
    lat = EXCLUDED.lat, lon = EXCLUDED.lon;
