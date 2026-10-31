# Gate 55 ask texts (gates/gate55/referee/review55.py)

## N0
There is no product owner to ask on this project: `tools/ask.py` will tell you so. Work from the spec and the examples.

## CQ
The product owner is available on his phone, though busy: ask him with `python3 /home/claude/hive/gates/gate68/referee/ask_owner.py 7681 "<your question>"`. Ask in plain business words, one decision per question; he answers in a sentence or two. (`tools/ask.py` is not used on this project.) **Before you build each function, ask him about every business decision its one-line spec leaves open**: cut-offs and boundaries, rounding, minimums and caps, what happens with blank, missing, negative or oddly formatted input. Build to his answers.

## SQ
The product owner is available on his phone, though busy: ask him with `python3 /home/claude/hive/gates/gate68/referee/ask_owner.py 7682 "<your question>"`. Ask in plain business words, one decision per question; he answers in a sentence or two. (`tools/ask.py` is not used on this project.) **Before you build each function, ask him about every business decision its one-line spec leaves open**: cut-offs and boundaries, rounding, minimums and caps, what happens with blank, missing, negative or oddly formatted input. Build to his answers. Your teammates ask him too: first read every answer he has given so far with `python3 /home/claude/hive/gates/gate68/referee/ask_owner.py 7682 --answers`, and do not ask again what he has already answered.

## SQH
There is no product owner to ask on this project: `tools/ask.py` will tell you so.

### The owner's rules for this feature (from his interview)
The owner decided each of these himself. Encode every one that touches your area as a test before you land, follow it exactly, and do not stretch it beyond the situation it describes.

- biz_days_add: Whenever a start date and a number of days n are given, the result is the ISO date (YYYY-MM-DD) reached by moving n business days forward from the start date, counting Monday to Friday only.
- biz_days_add: Whenever a day is skipped, it is because it is a Saturday, a Sunday, 25 December or 1 January (these two dates are holidays in every year); no other holidays exist.
- biz_days_add: Whenever n is negative, the date moves backward by that many business days, skipping weekends, 25 December and 1 January the same way (e.g. Monday 2024-03-04 minus 1 gives Friday 2024-03-01).
- biz_days_add: Whenever the start date falls on a Saturday or Sunday, it is first moved forward to the following Monday before counting, for positive, zero and negative n alike (Saturday 2024-03-02 plus 1 gives Tuesday 2024-03-05; Sunday 2024-03-03 minus 1 gives Friday 2024-03-01).
- biz_days_add: Whenever n is 0 and the start date is a weekday, the start date is returned unchanged; when n is 0 and the start is a weekend, the next Monday is returned.
- biz_days_add: Whenever the start date is itself 25 December or 1 January on a weekday, it is not moved and is returned as is for n = 0; counting then starts from that day (2024-12-25 plus 0 gives 2024-12-25, plus 1 gives 2024-12-26).
- biz_days_add: Whenever a weekend start date is moved to Monday and that Monday is 25 December or 1 January, the holiday date is returned as is for n = 0 (2028-12-23 plus 0 gives 2028-12-25).
- biz_days_add: Whenever n has a fractional part, it is cut toward zero before counting (2.9 counts as 2, -2.9 as -2, 0.5 and -0.5 as 0).
- biz_days_add: Whenever n is text that is wholly a number (e.g. '3', ' 3 ' with spaces, or '1e1' meaning 10), it is used as that number.
- biz_days_add: Whenever the start date or n is NULL, the result is NULL.
- biz_days_add: Whenever n is text that is not a number (including empty text), the result is NULL, even if the start date is also invalid.
- biz_days_add: Whenever the start date is not exactly four digits, hyphen, two digits, hyphen, two digits, or is not a real calendar date, the result is the text BAD_DATE; this covers '2024-02-30', '2024-2-3', empty text, a date with a time ('2024-03-01 10:00'), a date with leading spaces, and a plain number such as 20240301 (provided n is valid).
- biz_days_add: Whenever the counting would go past the supported calendar range (before year 1 or after 9999-12-31, e.g. 9999-12-30 plus 5, or a huge n like 1e30), the result is the text BAD_DATE.
- late_fee: Whenever days_late is 3 or fewer (including 0 and negative values), the fee is 0 (a grace period).
- late_fee: Whenever days_late is more than 3, the fee is 0.5% of the amount for every day late counted from day 1 (not only the days after the 3rd): 10000 cents 4 days late gives 200, 10 days late gives 500.
- late_fee: Whenever the percentage would exceed 25% of the amount (50 or more days late), the fee is capped at 25% of the amount (10000 cents gives 2500 for 50, 51 or more days).
- late_fee: Whenever the fee is not a whole number of cents, it is rounded up to the next whole cent (10001 cents at 4 days gives 201; 999 cents at 4 days gives 20; 1 cent at 4 days gives 1).
- late_fee: Whenever days_late has a fractional part and is above 3, the fraction counts (3.5 days on 10000 cents gives 175); 3.0001 days is above the grace period and is charged (100 cents gives 2).
- late_fee: Whenever amount_cents is 0, the fee is 0; whenever it is negative and days_late is over 3, the fee is negative at the same percentage, rounded up toward zero (-10000 cents at 10 days gives -500; at 100 days gives -2500); with 3 days or fewer the fee is 0.
- late_fee: Whenever either input is text that is wholly a number (e.g. '10000' and '10', spaces allowed), it is treated as that number.
- late_fee: Whenever either input is NULL, empty text or text that is not a number, the result is NULL.
- letter_grade: Whenever the score is first rounded to the nearest whole number (halves round up), the grade is A for 90 or more, B for 80 to 89, C for 70 to 79, D for 60 to 69 and F below 60.
- letter_grade: Whenever the score has a half-point at a boundary, it rounds up into the higher grade (89.5 gives A, 79.5 gives B, 69.5 gives C, 59.5 gives D), while 89.49 gives B and 59.49 gives F.
- letter_grade: Whenever the score is exactly 0, between 0 and 0.5, or exactly 100, the grade is F for 0 to 59.49 and A for 100.
- letter_grade: Whenever the raw score is below 0 (even -0.1 or -0.4) or above 100 (even 100.5), the result is the letter X, meaning invalid; the check uses the score before rounding.
- letter_grade: Whenever the score is text that is wholly a number (e.g. '85', ' 85 ', '1e2'), it is graded as that number.
- letter_grade: Whenever the score is NULL, empty text, spaces only or other non-numeric text, the result is NULL.
- loyalty_points: Whenever the tier is basic, bronze, an unrecognised name, empty text, NULL or a non-text value, points are 1 per unit of spend (spend 1000 gives 1000).
- loyalty_points: Whenever the tier is silver, points are 1.5 per unit of spend (1000 gives 1500); for gold, 2 per unit (1000 gives 2000).
- loyalty_points: Whenever the tier is written in different letter case or with spaces around it (GOLD, ' Gold ', Silver), it is recognised as that tier; but spaces inside a name (e.g. 'sil ver') are not, giving the 1-per-unit rate.
- loyalty_points: Whenever the calculated points are not a whole number, they are rounded down (999 at silver gives 1498; 10.99 at gold gives 21; 0.5 at basic gives 0; 3 at silver gives 4).
- loyalty_points: Whenever spend is negative, points are negative and rounding goes down, away from zero (-0.5 at basic gives -1; -10 at gold gives -20; -1 at silver gives -2).
- loyalty_points: Whenever spend is 0, points are 0.
- loyalty_points: Whenever spend is text that is wholly a number (e.g. '100', ' 100.5 ', '1e2'), it is used as that number ('100' at gold gives 200; ' 100.5 ' at gold gives 201).
- loyalty_points: Whenever spend is NULL, empty text or non-numeric text, the result is NULL, whatever the tier.
- loyalty_points: Spend is capped at 5000 before the tier multiplier is applied, so gold earns at most 10000 points. Whenever spend is extremely large (e.g. 1e30), the spend is capped at 5000 and the full whole-number result is returned.
- mask_card: Whenever a card number has at least 12 digits, the result shows the first 6 digits, then one asterisk for every digit in between, then the last 4 digits (4111111111111111 gives 411111******1111).
- mask_card: Whenever the card number contains spaces, hyphens or any other non-digit characters, those are removed first and only the digits are counted and shown (4111-1111-1111-1111 and '4111 1111 1111 1111' both give 411111******1111; letters inside are dropped too).
- mask_card: Whenever the card number has 12 to any larger number of digits, there is no maximum length: 12 digits give 2 asterisks, 19 digits give 9, 25 digits give 15.
- mask_card: Whenever fewer than 12 digits remain after removing non-digits (11 digits, empty text, spaces only, letters only like 'abcd'), the result is the text INVALID.
- mask_card: Whenever the card number is NULL, the result is NULL.
- mask_card: Whenever the card number is given as a plain number rather than text, it is treated as its digits and masked the same way.
- mask_card: Whenever digits are written in non-ASCII form (e.g. full-width digits), they are not counted as digits, so such input gives INVALID.
- mask_card: Whenever the card number has leading or trailing spaces, they are ignored and do not count as digits.
- pct_change: Whenever both values are given and old_value is not 0, the result is (new - old) / old x 100, rounded to one decimal place (100 to 150 gives 50.0; 100 to 50 gives -50.0; 100 to 100 gives 0.0).
- pct_change: Whenever old_value is 0 (including 0.0 and '0'), the result is 999.0 no matter what new_value is (0, positive or negative).
- pct_change: Whenever the rounding falls exactly on a half of a tenth, it rounds up in size, away from zero (1 to 1.0005 gives 0.1; 1 to 0.9995 gives -0.1; 1 to 1.00049 gives 0.0; 1 to 1.0095 gives 1.0).
- pct_change: Whenever a small decrease rounds to nothing, the result is shown as -0.0 rather than 0.0 (1 to 0.99951 gives -0.0).
- pct_change: Whenever old_value is negative, the percentage is divided by the negative old value itself, so the sign is reversed from what an increase would suggest (-100 to -50 gives -50.0; -100 to 50 gives -150.0; 100 to -50 gives -150.0; -3 to -4 gives 33.3).
- pct_change: Whenever either value is NULL, the result is NULL, even when old_value is 0 or new_value is 0.
- pct_change: Whenever either value is empty text or non-numeric text, the result is NULL, even when old_value is 0 ('0' to 'abc' gives NULL).
- pct_change: Whenever a value is text that is wholly a number (e.g. '100', ' 100 ', '1e2'), it is used as that number.
- ship_cost: Whenever the weight is above 0, the charge is a base of 300 cents plus a per-block charge for each started 500 g (weight divided by 500, rounded up): 100 cents per block in zone 1, 180 in zone 2 and 260 in zone 3.
- ship_cost: Whenever the weight is exactly on a 500 g multiple it counts that many blocks (500 g in zone 1 gives 400); one gram more starts a new block (501 g gives 500); even 0.5 g counts as one block.
- ship_cost: Whenever the weight is above 20000 g (20000 g exactly is not above), a flat surcharge of 2000 cents is added (20000 g zone 1 gives 4300; 20001 g zone 1 gives 6400; 20001 g zone 3 gives 12960).
- ship_cost: Whenever the zone is anything other than exactly 1 or 2 (0, 4, 99, negative, or fractional such as 1.5 or 2.5), the zone 3 rate of 260 per block is used.
- ship_cost: Whenever the zone is written as 2.0, '2' or ' 2 ', it counts as zone 2.
- ship_cost: Whenever the weight is 0 or negative, the charge is 0 (no base charge) for any valid zone, including an out-of-range zone.
- ship_cost: Whenever the weight or the zone is NULL, empty text or non-numeric text, the result is NULL, even if the other input is 0 or negative.
- ship_cost: Whenever the weight is text that is wholly a number (e.g. '500'), it is used as that number.
- slug: Whenever a title is given, it is turned into lower case, and each run of characters that are not a-z or 0-9 (spaces, tabs, line breaks, punctuation, underscores, hyphens, ampersands, symbols) is replaced by a single hyphen ('Hello,   World!' gives hello-world; 'a_b-c' gives a-b-c; 'a--b' gives a-b).
- slug: Whenever the title starts or ends with separators, no leading or trailing hyphen is kept ('  Hello World  ' gives hello-world).
- slug: Whenever the title contains accented or other non-English letters or digits (é, ü, ß, 日本語, ², ①), those characters are deleted entirely, without leaving a separator: 'naïve test' gives nave-test, 'Café Olé' gives caf-ol, 'abcédef' gives abcdef and 'Ünï Cödé' gives n-cd.
- slug: Whenever a non-ASCII character is a symbol or punctuation rather than a letter or digit (e.g. ¡, €, —, a non-breaking space), it acts as a separator and becomes a hyphen like other punctuation ('a€b' gives a-b; '¡Hola!' gives hola).
- slug: Whenever the slug would be longer than 30 characters, it is cut to the first 30 characters, even in the middle of a word, and if that leaves a hyphen at the end, the hyphen is removed (so it may be 29 characters).
- slug: Whenever the title is empty, spaces only, only symbols, or only deleted non-English letters (e.g. '', '   ', '!!!', '日本語', 'ß'), the result is n-a.
- slug: Whenever the title is NULL, the result is NULL.
- slug: Whenever the title is a number, it is converted to text first (123 gives 123; 12.5 gives 12-5).
- slug: Whenever the title contains digits, they are kept ('2024 Report' gives 2024-report).
- ticket_priority: Whenever severity is 1, 2, 3 or 4 (also 1.0 or the text '2'), the base priority is P1, P2, P3 or P4 respectively.
- ticket_priority: Whenever severity is any other number (0, 5, 9, negative, or fractional such as 2.5 or 3.99), the base priority is P4; fractions are not rounded.
- ticket_priority: Whenever hours_open is 48 or more, the priority is raised by one level (P4 to P3, P3 to P2, P2 to P1), but never above P1; 47.9 hours is not raised and exactly 48 is.
- ticket_priority: Whenever the severity is unrecognised (base P4) and the ticket has been open 48 hours or more, the result is P3 (severity 9, 0 or 2.5 at 48 hours gives P3).
- ticket_priority: Whenever hours_open is negative or under 48, there is no age bump, only the base priority applies; the bump does not go higher with more hours (severity 3 at 100 hours gives P2).
- ticket_priority: Whenever severity or hours_open is text that is wholly a number (e.g. '2' and '50', ' 2 ' and ' 50 ', '4.8e1'), it is used as that number.
- ticket_priority: Whenever severity or hours_open is NULL, empty text or non-numeric text, the result is NULL.
- avg_rating: Whenever a group of reviews is averaged, the result is the mean of the ratings, rounded to two decimals with halves rounding up (ratings 1, 1, 2 give 1.33; 4.5 and 4.4 give 4.45; 4.335 and 4.335 give 4.34).
- avg_rating: Whenever a rating is below 1 (0, 0.5, negative), it counts as 1 in the average, and whenever it is above 5 it counts as 5 (ratings 0 and 10 average 3.0).
- avg_rating: Whenever a rating is NULL or any text (empty text, non-numeric text, or a number written as text such as '3' or ' 4 '), that review is skipped and does not count in the average or the number of reviews. Only ratings stored as actual numbers are counted (abc, 4 and the text '3' average 4.0).
- avg_rating: Whenever a rating is text that is wholly a number (e.g. '3', ' 4 '), it is not converted to a number and is not counted: that review is skipped like any other text.
- avg_rating: Whenever the group has no reviews or no usable ratings (no rows, or only NULLs and text of any kind), the result is NULL.
- avg_rating: Whenever the DISTINCT form is used, each different rating value is counted once (ratings 1, 1, 2 average 1.5).
- A parcel recorded with 0 grams to zone 1 ships for free, with no base charge. The owner says: Yes, that's right. Everything looks fine.
