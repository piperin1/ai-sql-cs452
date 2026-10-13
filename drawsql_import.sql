-- Whisker Lounge Cat Cafe schema for drawsql.app
-- Import as PostgreSQL. Same tables and columns as schema.sql (the SQLite version the app uses),
-- written with explicit FOREIGN KEY lines so DrawSQL draws the relationships.

CREATE TABLE lounge (
    lounge_id    INTEGER PRIMARY KEY,
    name         VARCHAR(50)  NOT NULL UNIQUE,
    capacity     INTEGER      NOT NULL,
    hourly_rate  DECIMAL(6,2) NOT NULL,
    description  VARCHAR(255)
);

CREATE TABLE cat (
    cat_id        INTEGER PRIMARY KEY,
    name          VARCHAR(50)  NOT NULL,
    breed         VARCHAR(50)  NOT NULL,
    sex           CHAR(1)      NOT NULL,
    birth_date    DATE         NOT NULL,
    coat_color    VARCHAR(50)  NOT NULL,
    personality   VARCHAR(50),
    arrival_date  DATE         NOT NULL,
    status        VARCHAR(20)  NOT NULL,
    lounge_id     INTEGER,
    FOREIGN KEY (lounge_id) REFERENCES lounge (lounge_id)
);

CREATE TABLE staff (
    staff_id     INTEGER PRIMARY KEY,
    first_name   VARCHAR(50)  NOT NULL,
    last_name    VARCHAR(50)  NOT NULL,
    role         VARCHAR(30)  NOT NULL,
    hire_date    DATE         NOT NULL,
    hourly_wage  DECIMAL(6,2) NOT NULL
);

CREATE TABLE customer (
    customer_id      INTEGER PRIMARY KEY,
    first_name       VARCHAR(50)  NOT NULL,
    last_name        VARCHAR(50)  NOT NULL,
    email            VARCHAR(100) NOT NULL UNIQUE,
    join_date        DATE         NOT NULL,
    membership_tier  VARCHAR(10)  NOT NULL
);

CREATE TABLE visit (
    visit_id          INTEGER PRIMARY KEY,
    customer_id       INTEGER      NOT NULL,
    lounge_id         INTEGER      NOT NULL,
    visit_date        DATE         NOT NULL,
    start_time        TIME         NOT NULL,
    duration_minutes  INTEGER      NOT NULL,
    party_size        INTEGER      NOT NULL,
    cover_charge      DECIMAL(8,2) NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customer (customer_id),
    FOREIGN KEY (lounge_id) REFERENCES lounge (lounge_id)
);

CREATE TABLE menu_item (
    item_id   INTEGER PRIMARY KEY,
    name      VARCHAR(50)  NOT NULL UNIQUE,
    category  VARCHAR(20)  NOT NULL,
    price     DECIMAL(6,2) NOT NULL,
    is_vegan  BOOLEAN      NOT NULL
);

CREATE TABLE food_order (
    order_id    INTEGER PRIMARY KEY,
    visit_id    INTEGER NOT NULL,
    staff_id    INTEGER NOT NULL,
    order_time  TIME    NOT NULL,
    FOREIGN KEY (visit_id) REFERENCES visit (visit_id),
    FOREIGN KEY (staff_id) REFERENCES staff (staff_id)
);

CREATE TABLE order_item (
    order_id  INTEGER NOT NULL,
    item_id   INTEGER NOT NULL,
    quantity  INTEGER NOT NULL,
    PRIMARY KEY (order_id, item_id),
    FOREIGN KEY (order_id) REFERENCES food_order (order_id),
    FOREIGN KEY (item_id) REFERENCES menu_item (item_id)
);

CREATE TABLE adoption (
    adoption_id    INTEGER PRIMARY KEY,
    cat_id         INTEGER      NOT NULL UNIQUE,
    customer_id    INTEGER      NOT NULL,
    staff_id       INTEGER      NOT NULL,
    adoption_date  DATE         NOT NULL,
    fee            DECIMAL(6,2) NOT NULL,
    FOREIGN KEY (cat_id) REFERENCES cat (cat_id),
    FOREIGN KEY (customer_id) REFERENCES customer (customer_id),
    FOREIGN KEY (staff_id) REFERENCES staff (staff_id)
);

CREATE TABLE vet_visit (
    vet_visit_id  INTEGER PRIMARY KEY,
    cat_id        INTEGER      NOT NULL,
    visit_date    DATE         NOT NULL,
    reason        VARCHAR(20)  NOT NULL,
    vet_name      VARCHAR(50)  NOT NULL,
    cost          DECIMAL(8,2) NOT NULL,
    notes         VARCHAR(255),
    FOREIGN KEY (cat_id) REFERENCES cat (cat_id)
);
