-- Multi-constituency support. South Delhi remains the evidence-rich pilot
-- (official SEC/Census data); the four expansion constituencies carry
-- locality centroids and APPROXIMATE populations (labeled in indicators)
-- until their official ward loads.
CREATE TABLE IF NOT EXISTS constituencies (
    code  TEXT PRIMARY KEY,
    name  TEXT NOT NULL,
    state TEXT NOT NULL,
    lat   DOUBLE PRECISION NOT NULL,
    lon   DOUBLE PRECISION NOT NULL
);

INSERT INTO constituencies (code, name, state, lat, lon) VALUES
('south-delhi',       'South Delhi',       'Delhi',          28.525, 77.255),
('kolkata-dakshin',   'Kolkata Dakshin',   'West Bengal',    22.520, 88.350),
('ahmedabad-east',    'Ahmedabad East',    'Gujarat',        23.035, 72.660),
('mumbai-north-east', 'Mumbai North East', 'Maharashtra',    19.100, 72.925),
('chennai-south',     'Chennai South',     'Tamil Nadu',     12.970, 80.245)
ON CONFLICT (code) DO NOTHING;

ALTER TABLE wards   ADD COLUMN IF NOT EXISTS constituency TEXT DEFAULT 'south-delhi';
ALTER TABLE demands ADD COLUMN IF NOT EXISTS constituency TEXT DEFAULT 'south-delhi';
UPDATE wards   SET constituency = 'south-delhi' WHERE constituency IS NULL;
UPDATE demands SET constituency = 'south-delhi' WHERE constituency IS NULL;

INSERT INTO wards (ward_code, name, aliases, lat, lon, population, indicators, constituency) VALUES
-- Kolkata Dakshin (West Bengal)
('BALLYGUNGE',   'Ballygunge',      '{"ballygunj","বালিগঞ্জ"}',        22.5325, 88.3655,  90000, '{"colony_profile":"planned colony (approx.)","source":"approximate locality estimate (official ward data pending)"}', 'kolkata-dakshin'),
('KASBA',        'Kasba',           '{"কসবা"}',                        22.5177, 88.3832, 120000, '{"colony_profile":"dense mixed housing (approx.)","source":"approximate locality estimate (official ward data pending)"}', 'kolkata-dakshin'),
('BEHALA',       'Behala',          '{"বেহালা"}',                      22.4980, 88.3100, 180000, '{"colony_profile":"dense mixed, waterlogging-prone (approx.)","source":"approximate locality estimate (official ward data pending)"}', 'kolkata-dakshin'),
('TOLLYGUNGE',   'Tollygunge',      '{"টালিগঞ্জ"}',                     22.4986, 88.3453, 130000, '{"colony_profile":"dense mixed housing (approx.)","source":"approximate locality estimate (official ward data pending)"}', 'kolkata-dakshin'),
('BHAWANIPUR',   'Bhawanipur',      '{"bhowanipore","ভবানীপুর"}',      22.5354, 88.3435,  80000, '{"colony_profile":"planned colony (approx.)","source":"approximate locality estimate (official ward data pending)"}', 'kolkata-dakshin'),
('RASHBEHARI',   'Rashbehari',      '{"rash behari","রাসবিহারী"}',     22.5176, 88.3520,  70000, '{"colony_profile":"dense mixed housing (approx.)","source":"approximate locality estimate (official ward data pending)"}', 'kolkata-dakshin'),
-- Ahmedabad East (Gujarat)
('BAPUNAGAR',    'Bapunagar',       '{"બાપુનગર"}',                     23.0330, 72.6360, 150000, '{"colony_profile":"industrial working-class, chawl clusters (approx.)","source":"approximate locality estimate (official ward data pending)"}', 'ahmedabad-east'),
('NIKOL',        'Nikol',           '{"નિકોલ"}',                       23.0455, 72.6650, 160000, '{"colony_profile":"fast-growing periphery, unauthorized pockets (approx.)","source":"approximate locality estimate (official ward data pending)"}', 'ahmedabad-east'),
('VASTRAL',      'Vastral',         '{"વસ્ત્રાલ"}',                     23.0130, 72.6710, 120000, '{"colony_profile":"fast-growing periphery (approx.)","source":"approximate locality estimate (official ward data pending)"}', 'ahmedabad-east'),
('ODHAV',        'Odhav',           '{"ઓઢવ"}',                         23.0300, 72.6890, 110000, '{"colony_profile":"industrial belt, chawl clusters (approx.)","source":"approximate locality estimate (official ward data pending)"}', 'ahmedabad-east'),
('NARODA',       'Naroda',          '{"નરોડા"}',                       23.0710, 72.6560, 180000, '{"colony_profile":"industrial belt (approx.)","source":"approximate locality estimate (official ward data pending)"}', 'ahmedabad-east'),
('AMRAIWADI',    'Amraiwadi',       '{"અમરાઈવાડી"}',                   23.0090, 72.6350, 130000, '{"colony_profile":"industrial working-class (approx.)","source":"approximate locality estimate (official ward data pending)"}', 'ahmedabad-east'),
-- Mumbai North East (Maharashtra)
('GHATKOPAR',    'Ghatkopar',       '{"घाटकोपर"}',                     19.0790, 72.9080, 250000, '{"colony_profile":"dense mixed housing (approx.)","source":"approximate locality estimate (official ward data pending)"}', 'mumbai-north-east'),
('VIKHROLI',     'Vikhroli',        '{"विक्रोळी"}',                    19.1055, 72.9280, 160000, '{"colony_profile":"mixed housing with slum pockets (approx.)","source":"approximate locality estimate (official ward data pending)"}', 'mumbai-north-east'),
('BHANDUP',      'Bhandup',         '{"भांडुप"}',                      19.1440, 72.9370, 200000, '{"colony_profile":"dense mixed housing (approx.)","source":"approximate locality estimate (official ward data pending)"}', 'mumbai-north-east'),
('MULUND',       'Mulund',          '{"मुलुंड"}',                      19.1726, 72.9425, 220000, '{"colony_profile":"planned colony (approx.)","source":"approximate locality estimate (official ward data pending)"}', 'mumbai-north-east'),
('MANKHURD',     'Mankhurd',        '{"मानखुर्द"}',                    19.0480, 72.9310, 180000, '{"colony_profile":"slum & resettlement clusters (approx.)","source":"approximate locality estimate (official ward data pending)"}', 'mumbai-north-east'),
('GOVANDI',      'Govandi',         '{"shivaji nagar","गोवंडी"}',      19.0550, 72.9120, 200000, '{"colony_profile":"slum & resettlement clusters, lowest-HDI belt in Mumbai (approx.)","source":"approximate locality estimate (official ward data pending)"}', 'mumbai-north-east'),
-- Chennai South (Tamil Nadu)
('VELACHERY',    'Velachery',       '{"வேளச்சேரி"}',                   12.9755, 80.2207, 180000, '{"colony_profile":"flood-prone lakebed development (approx.)","source":"approximate locality estimate (official ward data pending)"}', 'chennai-south'),
('ADYAR',        'Adyar',           '{"அடையாறு"}',                     13.0067, 80.2565, 100000, '{"colony_profile":"planned colony (approx.)","source":"approximate locality estimate (official ward data pending)"}', 'chennai-south'),
('MYLAPORE',     'Mylapore',        '{"மயிலாப்பூர்"}',                  13.0339, 80.2695,  90000, '{"colony_profile":"old-city dense housing (approx.)","source":"approximate locality estimate (official ward data pending)"}', 'chennai-south'),
('SHOLINGANALLUR','Sholinganallur', '{"ஷோலிங்கநல்லூர்","omr"}',        12.9010, 80.2279, 150000, '{"colony_profile":"IT-corridor periphery, flood-prone (approx.)","source":"approximate locality estimate (official ward data pending)"}', 'chennai-south'),
('PERUNGUDI',    'Perungudi',       '{"பெருங்குடி"}',                  12.9654, 80.2461,  80000, '{"colony_profile":"IT-corridor periphery with slum pockets (approx.)","source":"approximate locality estimate (official ward data pending)"}', 'chennai-south'),
('BESANT_NAGAR', 'Besant Nagar',    '{"பெசன்ட் நகர்"}',                 13.0003, 80.2666,  60000, '{"colony_profile":"planned colony (approx.)","source":"approximate locality estimate (official ward data pending)"}', 'chennai-south')
ON CONFLICT (ward_code) DO UPDATE
SET name = EXCLUDED.name, aliases = EXCLUDED.aliases, lat = EXCLUDED.lat,
    lon = EXCLUDED.lon, population = EXCLUDED.population,
    indicators = EXCLUDED.indicators, constituency = EXCLUDED.constituency;
