-- Whisker Lounge Cat Cafe
-- A cat cafe where customers book time in themed lounges, order food and drinks,
-- and can adopt the cats that live there. The cafe also tracks staff and cat vet care.

CREATE TABLE lounge (
    lounge_id     INTEGER PRIMARY KEY,
    name          TEXT    NOT NULL UNIQUE,
    capacity      INTEGER NOT NULL,          -- max number of guests at one time
    hourly_rate   REAL    NOT NULL,          -- cover charge per guest per hour, in USD
    description   TEXT
);

CREATE TABLE cat (
    cat_id        INTEGER PRIMARY KEY,
    name          TEXT    NOT NULL,
    breed         TEXT    NOT NULL,
    sex           TEXT    NOT NULL CHECK (sex IN ('M', 'F')),
    birth_date    DATE    NOT NULL,
    coat_color    TEXT    NOT NULL,
    personality   TEXT,                      -- e.g. 'playful', 'shy', 'cuddly'
    arrival_date  DATE    NOT NULL,          -- date the cat came to the cafe
    status        TEXT    NOT NULL CHECK (status IN ('resident', 'adoptable', 'adopted')),
                                             -- resident = permanent cafe cat, not for adoption
    lounge_id     INTEGER REFERENCES lounge(lounge_id)   -- lounge the cat usually stays in; NULL once adopted
);

CREATE TABLE staff (
    staff_id      INTEGER PRIMARY KEY,
    first_name    TEXT    NOT NULL,
    last_name     TEXT    NOT NULL,
    role          TEXT    NOT NULL CHECK (role IN ('manager', 'barista', 'cat caretaker', 'adoption coordinator')),
    hire_date     DATE    NOT NULL,
    hourly_wage   REAL    NOT NULL
);

CREATE TABLE customer (
    customer_id     INTEGER PRIMARY KEY,
    first_name      TEXT    NOT NULL,
    last_name       TEXT    NOT NULL,
    email           TEXT    NOT NULL UNIQUE,
    join_date       DATE    NOT NULL,
    membership_tier TEXT    NOT NULL CHECK (membership_tier IN ('none', 'purr', 'meow', 'roar'))
                                             -- paid tiers from lowest to highest: purr, meow, roar
);

CREATE TABLE visit (
    visit_id          INTEGER PRIMARY KEY,
    customer_id       INTEGER NOT NULL REFERENCES customer(customer_id),
    lounge_id         INTEGER NOT NULL REFERENCES lounge(lounge_id),
    visit_date        DATE    NOT NULL,
    start_time        TEXT    NOT NULL,      -- 'HH:MM', 24-hour clock
    duration_minutes  INTEGER NOT NULL,
    party_size        INTEGER NOT NULL,      -- number of guests including the customer
    cover_charge      REAL    NOT NULL       -- total lounge fee paid for the visit, in USD
);

CREATE TABLE menu_item (
    item_id     INTEGER PRIMARY KEY,
    name        TEXT    NOT NULL UNIQUE,
    category    TEXT    NOT NULL CHECK (category IN ('coffee', 'tea', 'drink', 'pastry', 'snack')),
    price       REAL    NOT NULL,
    is_vegan    INTEGER NOT NULL CHECK (is_vegan IN (0, 1))
);

CREATE TABLE food_order (
    order_id    INTEGER PRIMARY KEY,
    visit_id    INTEGER NOT NULL REFERENCES visit(visit_id),
    staff_id    INTEGER NOT NULL REFERENCES staff(staff_id),   -- staff member who served the order
    order_time  TEXT    NOT NULL                               -- 'HH:MM', 24-hour clock
);

CREATE TABLE order_item (
    order_id    INTEGER NOT NULL REFERENCES food_order(order_id),
    item_id     INTEGER NOT NULL REFERENCES menu_item(item_id),
    quantity    INTEGER NOT NULL,
    PRIMARY KEY (order_id, item_id)
);

CREATE TABLE adoption (
    adoption_id    INTEGER PRIMARY KEY,
    cat_id         INTEGER NOT NULL UNIQUE REFERENCES cat(cat_id),
    customer_id    INTEGER NOT NULL REFERENCES customer(customer_id),
    staff_id       INTEGER NOT NULL REFERENCES staff(staff_id),   -- staff member who handled the adoption
    adoption_date  DATE    NOT NULL,
    fee            REAL    NOT NULL
);

CREATE TABLE vet_visit (
    vet_visit_id  INTEGER PRIMARY KEY,
    cat_id        INTEGER NOT NULL REFERENCES cat(cat_id),
    visit_date    DATE    NOT NULL,
    reason        TEXT    NOT NULL CHECK (reason IN ('checkup', 'vaccination', 'dental', 'illness', 'injury', 'spay/neuter')),
    vet_name      TEXT    NOT NULL,
    cost          REAL    NOT NULL,
    notes         TEXT
);
