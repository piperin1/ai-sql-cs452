# Example results

Model: `openai:gpt-5-mini` · Run: 2026-10-11 17:24

Each answer is marked correct when the model's query returns the same rows as a hand-written reference query. (Re-graded after fixing the checker: it originally marked combined name columns and pivoted layouts as wrong.)

## Score by strategy

| Strategy | Correct |
|---|---|
| zero_shot | 10 / 10 |
| single_domain | 10 / 10 |
| cross_domain | 10 / 10 |

## 1. Which cats are available for adoption right now, and which lounge is each one in?

### zero_shot — ✅ correct

```sql
SELECT c.cat_id, c.name AS cat_name, c.breed, c.sex, c.birth_date, c.coat_color, c.personality, l.name AS lounge_name
FROM cat c
LEFT JOIN lounge l ON c.lounge_id = l.lounge_id
WHERE c.status = 'adoptable';
```

**Answer:** These cats are adoptable right now and where to find them in the cafe:

- Pepper — Garden Patio  
- Ziggy — Kitten Corner  
- Hazel — Library Nook  
- Sushi — Kitten Corner  
- Pixel — Sunbeam Room  
- Tofu — Kitten Corner  
- Duchess — Library Nook  
- Rocket — Garden Patio  
- Bean — Kitten Corner  
- Chai — Sunbeam Room

### single_domain — ✅ correct

```sql
SELECT c.name AS cat_name, l.name AS lounge_name
FROM cat c
LEFT JOIN lounge l ON c.lounge_id = l.lounge_id
WHERE c.status = 'adoptable'
ORDER BY c.name;
```

**Answer:** Right now the following cats are available for adoption: Bean — Kitten Corner; Chai — Sunbeam Room; Duchess — Library Nook; Hazel — Library Nook; Pepper — Garden Patio; Pixel — Sunbeam Room; Rocket — Garden Patio; Sushi — Kitten Corner; Tofu — Kitten Corner; Ziggy — Kitten Corner. 

Want more details on any of them or help starting the adoption process?

### cross_domain — ✅ correct

```sql
SELECT c.cat_id, c.name, c.breed, l.name AS lounge_name FROM cat c LEFT JOIN lounge l ON c.lounge_id = l.lounge_id WHERE c.status = 'adoptable' ORDER BY c.name;
```

**Answer:** Here are the cats available for adoption and where to find them: Bean (Kitten Corner), Chai (Sunbeam Room), Duchess (Library Nook), Hazel (Library Nook), Pepper (Garden Patio), Pixel (Sunbeam Room), Rocket (Garden Patio), Sushi (Kitten Corner), Tofu (Kitten Corner), Ziggy (Kitten Corner).

<details><summary>Reference query</summary>

```sql
SELECT c.name, l.name FROM cat c JOIN lounge l ON c.lounge_id = l.lounge_id WHERE c.status = 'adoptable';
```
</details>

## 2. What is our best-selling menu item by number sold?

### zero_shot — ✅ correct

```sql
SELECT m.name, SUM(oi.quantity) AS total_sold
FROM order_item oi
JOIN menu_item m ON oi.item_id = m.item_id
GROUP BY m.item_id, m.name
ORDER BY total_sold DESC
LIMIT 1;
```

**Answer:** Our best-selling menu item is the Purr-fect Latte — 306 sold.

### single_domain — ✅ correct

```sql
SELECT m.name, SUM(oi.quantity) AS total_sold
FROM menu_item m
JOIN order_item oi ON m.item_id = oi.item_id
GROUP BY m.item_id, m.name
ORDER BY total_sold DESC
LIMIT 1;
```

**Answer:** Our best-selling item is the Purr-fect Latte — we've sold 306 of them.

### cross_domain — ✅ correct

```sql
SELECT mi.name, SUM(oi.quantity) AS total_sold FROM order_item oi JOIN menu_item mi ON oi.item_id = mi.item_id GROUP BY mi.item_id ORDER BY total_sold DESC LIMIT 1;
```

**Answer:** Our best-selling item is the Purr-fect Latte — we've sold 306 of them.

<details><summary>Reference query</summary>

```sql
SELECT m.name FROM order_item oi JOIN menu_item m ON oi.item_id = m.item_id GROUP BY m.item_id ORDER BY SUM(oi.quantity) DESC LIMIT 1;
```
</details>

## 3. Which lounge brought in the most cover charge money during June, July and August 2026?

### zero_shot — ✅ correct

```sql
SELECT l.name, SUM(v.cover_charge) AS total_cover
FROM lounge l
JOIN visit v ON l.lounge_id = v.lounge_id
WHERE v.visit_date BETWEEN '2026-06-01' AND '2026-08-31'
GROUP BY l.lounge_id, l.name
HAVING SUM(v.cover_charge) = (
  SELECT MAX(sumc) FROM (
    SELECT SUM(cover_charge) AS sumc FROM visit
    WHERE visit_date BETWEEN '2026-06-01' AND '2026-08-31'
    GROUP BY lounge_id
  )
);
```

**Answer:** The Sunbeam Room brought in the most cover charge money during June–August 2026, totaling $3,465.

### single_domain — ✅ correct

```sql
SELECT l.name, SUM(v.cover_charge) AS total_cover
FROM visit v
JOIN lounge l ON v.lounge_id = l.lounge_id
WHERE v.visit_date BETWEEN '2026-06-01' AND '2026-08-31'
GROUP BY l.lounge_id, l.name
HAVING SUM(v.cover_charge) = (
  SELECT MAX(total) FROM (
    SELECT SUM(v2.cover_charge) AS total
    FROM visit v2
    WHERE v2.visit_date BETWEEN '2026-06-01' AND '2026-08-31'
    GROUP BY v2.lounge_id
  )
);
```

**Answer:** The Sunbeam Room brought in the most cover charge money during June–August 2026, totaling $3,465.

### cross_domain — ✅ correct

```sql
SELECT l.name FROM lounge l JOIN visit v ON l.lounge_id = v.lounge_id WHERE v.visit_date BETWEEN '2026-06-01' AND '2026-08-31' GROUP BY l.lounge_id ORDER BY SUM(v.cover_charge) DESC LIMIT 1;
```

**Answer:** The Sunbeam Room brought in the most cover charge money during June–August 2026. Would you like the exact totals or a month-by-month breakdown?

<details><summary>Reference query</summary>

```sql
SELECT l.name FROM visit v JOIN lounge l ON v.lounge_id = l.lounge_id WHERE v.visit_date BETWEEN '2026-06-01' AND '2026-08-31' GROUP BY l.lounge_id ORDER BY SUM(v.cover_charge) DESC LIMIT 1;
```
</details>

## 4. Who adopted Gizmo, and when?

### zero_shot — ✅ correct

```sql
SELECT c.first_name || ' ' || c.last_name AS adopter, a.adoption_date FROM adoption a JOIN cat ct ON a.cat_id = ct.cat_id JOIN customer c ON a.customer_id = c.customer_id WHERE ct.name = 'Gizmo';
```

**Answer:** Gizmo was adopted by Emma Brown on March 28, 2026.

### single_domain — ✅ correct

```sql
SELECT customer.first_name || ' ' || customer.last_name AS adopter, adoption.adoption_date
FROM adoption
JOIN cat ON adoption.cat_id = cat.cat_id
JOIN customer ON adoption.customer_id = customer.customer_id
WHERE cat.name = 'Gizmo';
```

**Answer:** Gizmo was adopted by Emma Brown on March 28, 2026.

### cross_domain — ✅ correct

```sql
SELECT c.first_name || ' ' || c.last_name AS adopter, a.adoption_date
FROM adoption a
JOIN cat ct ON a.cat_id = ct.cat_id
JOIN customer c ON a.customer_id = c.customer_id
WHERE ct.name = 'Gizmo';
```

**Answer:** Gizmo was adopted by Emma Brown on 2026-03-28.

<details><summary>Reference query</summary>

```sql
SELECT cu.first_name, cu.last_name, a.adoption_date FROM adoption a JOIN cat c ON a.cat_id = c.cat_id JOIN customer cu ON a.customer_id = cu.customer_id WHERE c.name = 'Gizmo';
```
</details>

## 5. Which three cats have cost the most in vet bills in 2026?

### zero_shot — ✅ correct

```sql
SELECT c.cat_id, c.name, SUM(v.cost) AS total_cost
FROM cat c
JOIN vet_visit v ON c.cat_id = v.cat_id
WHERE strftime('%Y', v.visit_date) = '2026'
GROUP BY c.cat_id, c.name
ORDER BY total_cost DESC
LIMIT 3;
```

**Answer:** The top three cats with the highest vet bills in 2026 were Mochi ($642.00), Tofu ($641.00), and Ziggy ($479.00).

### single_domain — ✅ correct

```sql
SELECT c.name, SUM(vv.cost) AS total_vet_cost
FROM vet_visit vv
JOIN cat c ON vv.cat_id = c.cat_id
WHERE vv.visit_date >= '2026-01-01' AND vv.visit_date <= '2026-12-31'
GROUP BY c.cat_id, c.name
ORDER BY total_vet_cost DESC
LIMIT 3;
```

**Answer:** The three cats with the highest vet bills in 2026 are Mochi ($642.00), Tofu ($641.00), and Ziggy ($479.00).

### cross_domain — ✅ correct

```sql
SELECT c.cat_id, c.name, SUM(v.cost) AS total_cost
FROM vet_visit v JOIN cat c ON v.cat_id = c.cat_id
WHERE v.visit_date BETWEEN '2026-01-01' AND '2026-12-31'
GROUP BY c.cat_id, c.name
ORDER BY total_cost DESC
LIMIT 3;
```

**Answer:** The top three cats by vet bill totals for 2026 are Mochi ($642.00), Tofu ($641.00), and Ziggy ($479.00).

<details><summary>Reference query</summary>

```sql
SELECT c.name FROM vet_visit vv JOIN cat c ON vv.cat_id = c.cat_id WHERE vv.visit_date BETWEEN '2026-01-01' AND '2026-12-31' GROUP BY c.cat_id ORDER BY SUM(vv.cost) DESC LIMIT 3;
```
</details>

## 6. Which barista has served the most orders?

### zero_shot — ✅ correct

```sql
SELECT s.staff_id, s.first_name, s.last_name, COUNT(*) AS orders_served
FROM food_order f
JOIN staff s ON f.staff_id = s.staff_id
WHERE s.role = 'barista'
GROUP BY s.staff_id, s.first_name, s.last_name
ORDER BY orders_served DESC
LIMIT 1;
```

**Answer:** Maya Thompson has served the most orders — 340 in total.

### single_domain — ✅ correct

```sql
SELECT s.first_name, s.last_name, COUNT(*) AS orders_served FROM food_order o JOIN staff s ON o.staff_id = s.staff_id WHERE s.role = 'barista' GROUP BY s.staff_id ORDER BY orders_served DESC LIMIT 1;
```

**Answer:** Maya Thompson is the barista who’s served the most orders — 340 in total. Great work, Maya!

### cross_domain — ✅ correct

```sql
SELECT s.staff_id, s.first_name, s.last_name, COUNT(*) AS orders
FROM staff s JOIN food_order fo ON s.staff_id = fo.staff_id
WHERE s.role = 'barista'
GROUP BY s.staff_id
ORDER BY orders DESC
LIMIT 1;
```

**Answer:** Maya Thompson has served the most orders — 340.

<details><summary>Reference query</summary>

```sql
SELECT s.first_name, s.last_name FROM food_order f JOIN staff s ON f.staff_id = s.staff_id WHERE s.role = 'barista' GROUP BY s.staff_id ORDER BY COUNT(*) DESC LIMIT 1;
```
</details>

## 7. Is the average party size bigger on weekends or weekdays?

### zero_shot — ✅ correct

```sql
SELECT CASE
  WHEN w.avg IS NULL AND d.avg IS NULL THEN 'no_data'
  WHEN w.avg IS NULL THEN 'weekday'
  WHEN d.avg IS NULL THEN 'weekend'
  WHEN w.avg > d.avg THEN 'weekend'
  WHEN w.avg < d.avg THEN 'weekday'
  ELSE 'equal'
END AS bigger,
w.avg AS weekend_avg,
d.avg AS weekday_avg
FROM (SELECT AVG(party_size) AS avg FROM visit WHERE strftime('%w', visit_date) IN ('0','6')) w,
     (SELECT AVG(party_size) AS avg FROM visit WHERE strftime('%w', visit_date) IN ('1','2','3','4','5')) d;
```

**Answer:** Weekends are slightly bigger. The average party size on weekends is about 2.41 people versus about 2.39 on weekdays — a very small difference (≈0.02).

### single_domain — ✅ correct

```sql
SELECT CASE WHEN strftime('%w', visit_date) IN ('0','6') THEN 'weekend' ELSE 'weekday' END AS period, AVG(party_size) AS avg_party_size
FROM visit
GROUP BY CASE WHEN strftime('%w', visit_date) IN ('0','6') THEN 'weekend' ELSE 'weekday' END
ORDER BY avg_party_size DESC
LIMIT 1;
```

**Answer:** The average party size is bigger on weekends. On weekends the average party size is about 2.41 people.

### cross_domain — ✅ correct

```sql
SELECT CASE
    WHEN t.weekend_avg IS NULL AND t.weekday_avg IS NULL THEN 'no data'
    WHEN t.weekend_avg > t.weekday_avg THEN 'weekend'
    WHEN t.weekend_avg < t.weekday_avg THEN 'weekday'
    ELSE 'equal'
END AS bigger, t.weekend_avg, t.weekday_avg
FROM (
    SELECT
        AVG(CASE WHEN strftime('%w', visit_date) IN ('0','6') THEN party_size END) AS weekend_avg,
        AVG(CASE WHEN strftime('%w', visit_date) IN ('1','2','3','4','5') THEN party_size END) AS weekday_avg
    FROM visit
) AS t;
```

**Answer:** Slightly bigger on weekends — the average party size is about 2.41 on weekends versus about 2.39 on weekdays.

<details><summary>Reference query</summary>

```sql
SELECT CASE WHEN AVG(CASE WHEN strftime('%w', visit_date) IN ('0', '6') THEN party_size END) > AVG(CASE WHEN strftime('%w', visit_date) NOT IN ('0', '6') THEN party_size END) THEN 'weekend' ELSE 'weekday' END FROM visit;
```
</details>

## 8. Which customers with the top membership tier have visited more than 25 times?

### zero_shot — ✅ correct

```sql
SELECT c.customer_id, c.first_name, c.last_name, c.email, COUNT(v.visit_id) AS visit_count
FROM customer c
JOIN visit v ON c.customer_id = v.customer_id
WHERE c.membership_tier = 'roar'
GROUP BY c.customer_id
HAVING COUNT(v.visit_id) > 25
ORDER BY visit_count DESC;
```

**Answer:** One customer fits that criteria: Henry Hernandez (customer ID 14), henry.hernandez@example.com — 27 visits.

### single_domain — ✅ correct

```sql
SELECT c.customer_id, c.first_name, c.last_name, c.email, COUNT(v.visit_id) AS visits
FROM customer c
JOIN visit v ON v.customer_id = c.customer_id
WHERE c.membership_tier = 'roar'
GROUP BY c.customer_id, c.first_name, c.last_name, c.email
HAVING COUNT(v.visit_id) > 25;
```

**Answer:** Henry Hernandez (customer ID 14, henry.hernandez@example.com) — 27 visits. He's the only top-tier customer with more than 25 visits.

### cross_domain — ✅ correct

```sql
SELECT c.customer_id, c.first_name, c.last_name, COUNT(v.visit_id) AS visit_count
FROM customer c
JOIN visit v ON v.customer_id = c.customer_id
WHERE c.membership_tier = 'roar'
GROUP BY c.customer_id
HAVING COUNT(v.visit_id) > 25
ORDER BY visit_count DESC;
```

**Answer:** The only customer meeting that criteria is Henry Hernandez (customer ID 14), with 27 visits.

<details><summary>Reference query</summary>

```sql
SELECT cu.first_name, cu.last_name FROM visit v JOIN customer cu ON v.customer_id = cu.customer_id WHERE cu.membership_tier = 'roar' GROUP BY cu.customer_id HAVING COUNT(*) > 25;
```
</details>

## 9. How many vegan items have been ordered in total?

### zero_shot — ✅ correct

```sql
SELECT COALESCE(SUM(oi.quantity), 0) AS total_vegan_items FROM order_item oi JOIN menu_item m ON oi.item_id = m.item_id WHERE m.is_vegan = 1;
```

**Answer:** So far, a total of 863 vegan items have been ordered.

### single_domain — ✅ correct

```sql
SELECT COALESCE(SUM(oi.quantity), 0) AS total_vegan_items_ordered FROM order_item oi JOIN menu_item m ON oi.item_id = m.item_id WHERE m.is_vegan = 1;
```

**Answer:** We’ve had 863 vegan items ordered in total.

### cross_domain — ✅ correct

```sql
SELECT COALESCE(SUM(oi.quantity), 0) AS total_vegan_items FROM order_item oi JOIN menu_item mi ON oi.item_id = mi.item_id WHERE mi.is_vegan = 1;
```

**Answer:** So far, a total of 863 vegan items have been ordered.

<details><summary>Reference query</summary>

```sql
SELECT SUM(oi.quantity) FROM order_item oi JOIN menu_item m ON oi.item_id = m.item_id WHERE m.is_vegan = 1;
```
</details>

## 10. Which cat currently living at the cafe has been here the longest?

### zero_shot — ✅ correct

```sql
SELECT cat_id, name, breed, arrival_date, status, lounge_id
FROM cat
WHERE status IN ('resident','adoptable')
  AND arrival_date = (
    SELECT MIN(arrival_date) FROM cat WHERE status IN ('resident','adoptable')
);
```

**Answer:** Clover, a Maine Coon, has been here the longest — she arrived on 2022-08-09 and is a resident in lounge 4.

### single_domain — ✅ correct

```sql
SELECT cat_id, name, breed, arrival_date, status
FROM cat
WHERE status IN ('resident','adoptable')
  AND arrival_date = (
    SELECT MIN(arrival_date) FROM cat WHERE status IN ('resident','adoptable')
  );
```

**Answer:** Clover, our Maine Coon resident, has been here the longest — she arrived on August 9, 2022.

### cross_domain — ✅ correct

```sql
SELECT cat_id, name, breed, arrival_date, status, lounge_id
FROM cat
WHERE status IN ('resident', 'adoptable')
  AND arrival_date = (SELECT MIN(arrival_date) FROM cat WHERE status IN ('resident', 'adoptable'));
```

**Answer:** Clover, a Maine Coon, has been here the longest — she arrived on 2022-08-09 and is currently a resident in Lounge 4.

<details><summary>Reference query</summary>

```sql
SELECT name FROM cat WHERE status != 'adopted' ORDER BY arrival_date LIMIT 1;
```
</details>

---
Tokens used: 38613 input / 18616 output
