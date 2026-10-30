# Gate 55 ask texts (gates/gate55/referee/review55.py)

## N0
There is no product owner to ask on this project: `tools/ask.py` will tell you so. Work from the spec and the examples.

## B
There is no product owner to ask on this project: `tools/ask.py` will tell you so. Work from the spec and the examples.

## SL
There is no product owner to ask on this project: `tools/ask.py` will tell you so.

### The owner's rules for this feature (from his interview)
The owner decided each of these himself. Encode every one that touches your area as a test before you land, follow it exactly, and do not stretch it beyond the situation it describes.

- biz_days_between: Whenever two valid dates are given, it counts the Monday-to-Friday days from the start date up to but not including the end date, so the start day counts if it is a weekday and the end day never counts (Monday 2024-01-01 to Monday 2024-01-08 gives 5; Friday to the next Monday gives 1).
- biz_days_between: Whenever the start and end dates are the same day, it returns 0.
- biz_days_between: Whenever the end date is earlier than the start date, it counts the weekdays in the same way between the two dates and returns the result as a negative number (2024-01-08 back to 2024-01-01 gives -5).
- biz_days_between: Whenever the period contains only Saturdays and Sundays, it returns 0; a weekend start day is not counted but a weekend end day is simply excluded like any end day.
- biz_days_between: Saturdays and Sundays are skipped, and Jan 1 and Dec 25 are non-working days. No other holidays count; all other public holidays are counted as ordinary working days.
- biz_days_between: Whenever either date is NULL, it returns NULL.
- biz_days_between: Whenever either date is empty text, unreadable text (such as 'abc'), a number such as 2024, or a non-existent calendar date (such as 2024-02-30 or month 13), it returns NULL rather than an error or 0.
- biz_days_between: Whenever a date is written with a time after it (such as '2024-01-01 10:00:00' or '2024-01-01T09:00'), the time is ignored and only the first 10 characters are used as the date.
- biz_days_between: Whenever a date has extra text after its first 10 characters (such as '2024-01-10abc'), the extra text is ignored and the date is accepted; spaces around the date are also ignored.
- biz_days_between: Whenever a date is written with slashes ('2024/01/10'), without zero padding ('2024-1-10') or with a one-digit day ('2024-01-1'), it returns NULL; compact digits ('20240110') and ISO week dates ('2024-W01-1') are however accepted as valid dates, as is the number 20240110.
- fmt_phone: Whenever the text contains exactly 10 digits after ignoring everything that is not a digit, it returns the number as (AAA) BBB-CCCC, whatever the separators were (dashes, dots, spaces, brackets, plus sign).
- fmt_phone: Whenever the text contains exactly 11 digits and the first digit is 1, it drops that leading 1 and formats the remaining 10 digits as (AAA) BBB-CCCC (so '+1 555 123 4567' and '15551234567' both give '(555) 123-4567').
- fmt_phone: Whenever the text does not end up with exactly 10 digits, it returns an empty string instead of the original text. This covers 11 digits that do not start with 1 (such as '2 555 123 4567'), fewer than 10 digits, 12 or more digits, and an international number like '+44 20 7946 0958'. An extension like 'ext 89' is not counted as part of the 10 digits. When the number itself is valid, the extension is appended to it as ' x89'.
- fmt_phone: Whenever letters or other words are mixed in with exactly 10 digits (such as 'CALL-555-123-4567'), the non-digit characters are thrown away and the number is formatted; but a vanity number with letters instead of digits ('1-800-FLOWERS') has too few digits and is returned unchanged.
- fmt_phone: Whenever the area code or exchange begins with 0 or 1 (such as '0551234567'), it is still formatted as-is ('(055) 123-4567'); no check is made that the number is a valid North American number. Only a single leading 1 on an 11-digit number is removed.
- fmt_phone: Whenever the input is NULL, it returns NULL; whenever it is empty text, it returns empty text; whenever it has no digits ('abc'), it returns the text unchanged.
- fmt_phone: Whenever the input is a plain number rather than text (such as 5551234567 or 15551234567), it is treated as its digits and formatted; a decimal number such as 5551234567.0 is returned as the text '5551234567.0' because the extra digit makes 11 digits not starting with 1.
- fmt_phone: Whenever the digits are written in non-Western numerals (such as Arabic-Indic digits), they are not recognised as digits and the text is returned unchanged.
- grade_letter: Whenever the score is 92 or more it returns 'A'; 83 or more but under 92 returns 'B'; 71 or more but under 83 returns 'C'; 60 or more but under 71 returns 'D'; anything lower returns 'F'.
- grade_letter: Whenever the score is exactly on a boundary (90, 80, 70, 60) it gets the higher grade; scores are never rounded, so 89.99 or 89.9999999 is a 'B' and 59.99 is an 'F'.
- grade_letter: Whenever the score is above 100 or below 0 it returns 'X'. Exactly 0 is valid and returns 'F'. Exactly 100 is valid and returns 'A'.
- grade_letter: Whenever the score is NULL, it returns NULL.
- grade_letter: Whenever the score is text holding a number ('95', ' 85 ', '89.5', '1e2'), it is read as that number; text that starts with a number ('85%', '90abc') uses the leading number.
- grade_letter: Whenever the score is empty text, text with no leading number ('abc', 'A', '-', '0x5A'), or the boolean true, it is treated as 0 and returns 'F' rather than NULL.
- late_fee: Whenever an invoice is late by a positive number of days, the first 5 days late are free, so only the days beyond the 5th are charged. An invoice late by 5 days or fewer has no fee. For each charged day the fee is 0.5% of the invoice amount in cents, and the total is rounded down to a whole number of cents. The fee has a minimum of 500 cents, and it is capped at 20% of the invoice amount in cents, rounded down. The cap wins over the minimum, so on a small invoice where 20% of the invoice is less than 500 cents, the fee is that 20% amount. Example: 10000 cents, 10 days late: 5 charged days give 250, raised to the 500 minimum, so the fee is 500. The cap here is 2000.
- late_fee: Whenever the fee is not a whole number of cents, it is rounded to the nearest cent with exact halves rounded up (100 cents for 3 days gives 2; 1 cent for 100 days gives 1; 1 cent for 99 days gives 0; 99 cents for 10 days gives 5).
- late_fee: Whenever days late is zero or negative (not late), or the invoice amount is zero or negative, the fee is 0.
- late_fee: Whenever either the amount or the days late is NULL, it returns NULL.
- late_fee: Whenever days late is a fraction (such as 1.5) it is used as is in the calculation (10000 cents for 1.5 days gives 75), and a fractional amount (1000.5) is used as is before the final rounding to a whole cent.
- late_fee: Whenever the amount or days late is text, a number in the text is used ('10000' and '10' give 500; '3 days' counts as 3); empty text or text with no leading number counts as 0, so the fee is 0 and not NULL.
- shipping_cost: Whenever the weight and zone are valid, the charge is zone x (300 + 100 x the number of started kilograms) cents, where any part of a kilogram counts as a whole one (500 g in zone 1 gives 400; exactly 1000 g gives 400; 1001 g gives 500; 2500 g in zone 2 gives 1200).
- shipping_cost: Whenever the weight is exactly 0, the charge is the base amount only: zone x 300 cents (zone 3 gives 900), and the fractional weight 0.5 g counts as one started kilogram.
- shipping_cost: Whenever the weight is negative, it returns NULL.
- shipping_cost: A zone that is not a number at all (empty text, 'abc', 'A'), is not a whole number (1.5), or is outside 1 to 3 (below 1, meaning zero or negative, or above 3) is billed as zone 3, and it does not return NULL. A whole-valued zone like 2.0 or '1.0' is accepted as that zone number. There is no zone above 3, so zone 100 is billed as zone 3.
- shipping_cost: Whenever the weight or zone is NULL, it returns NULL.
- shipping_cost: Whenever the weight is text, a number in the text is used ('500', '2kg' counts as 2 g); empty text or text with no leading number counts as a weight of 0 (charged only the base amount), while text with a leading number in the zone ('2z' is zone 2) is accepted.
- shipping_cost: Whenever the weight is over 30000 g, the charge is a flat 9999, whatever the zone (for example, 1,000,000,000 g in zone 1 gives 9999). A weight of exactly 30000 g is priced normally.
- tiered_price: Whenever the quantity is under 10, the total is the unit price times the quantity with no discount (250 cents x 5 gives 1250).
- tiered_price: Whenever the quantity is 10 to 49 units, the whole order, not just the units above 10, gets 10% off (250 x 10 gives 2250; 250 x 11 gives 2475), so 10 units can cost the same as 9 units (2250 each). Whenever the quantity is 50 or more, the whole order gets 20% off.
- tiered_price: The total is rounded to the nearest 5 cents, with exact halves rounded up, so the total is always a multiple of 5 cents (1 cent x 10 gives 10; 1 cent x 15 gives 15; 1 cent x 25 gives 25; 99.5 cents x 3 gives 300).
- tiered_price: Whenever the quantity is 0 or the unit price is 0, the total is 0.
- tiered_price: Whenever the unit price or quantity is negative, it returns NULL.
- tiered_price: Whenever either the unit price or quantity is NULL, it returns NULL.
- tiered_price: Whenever the quantity is a fraction, it is used as is and the discount applies only when it is 10 or more (9.99 gives no discount, 250 x 9.99 gives 2498; 10.0 gets the discount).
- tiered_price: Whenever the price or quantity is text, a number in the text is used ('250' and '10' give 2250; '12x' counts as 12); empty text or text with no leading number counts as 0, so the total is 0 and not NULL.
- weighted_rating: Whenever the rating and the number of votes are valid, the result is (votes x average rating + 30) / (votes + 10), that is the average pulled toward a neutral prior of 3.0 that is worth 10 votes (5.0 with 10 votes gives 4.0; 4.5 with 100 votes gives 4.36).
- weighted_rating: Whenever the result is calculated, it is rounded to 2 decimal places with exact halves rounded up, and is returned as a decimal number (4.0, not 4).
- weighted_rating: Whenever there are fewer than 5 votes, including 0 votes, the result is NULL. Exactly 5 votes is accepted.
- weighted_rating: Whenever the votes are negative, it returns NULL; whenever either the rating or the votes are NULL, it returns NULL.
- weighted_rating: Whenever the average rating lies outside any normal scale (0, negative or above 5, such as -2 or 7), it is not rejected or limited and is used as given (rating 0 with 10 votes gives 1.5; rating 7 with 10 votes gives 5.0).
- weighted_rating: Whenever the votes are a fraction (2.5), they are used as is in the calculation.
- weighted_rating: Whenever the rating or votes are text, a number in the text is used ('5' and '10' give 4.0); empty text or text with no leading number counts as 0, so a rating of 'abc' counts as rating 0 (giving 1.5 with 10 votes) and votes of 'abc' counts as 0 votes (giving 3.0).
- gross_receipts: Whenever a group of rows is totalled, it adds up only the amounts that are greater than zero; negative amounts (refunds) are left out and not subtracted (100, -50, 300 gives 400).
- gross_receipts: Whenever an amount is NULL or exactly 0, it adds nothing to the total.
- gross_receipts: Whenever there are no rows, only NULL amounts, or only zero or negative amounts, the total is 0, not NULL. Correction from the owner, which overrides anything above that it contradicts: It should return NULL, not 0, when there are no valid rows.
- gross_receipts: Whenever every counted amount is a whole number, the total is a whole number; whenever any counted amount has decimals the total is a decimal number (100.5 and 200 give 300.5), using ordinary floating point addition (0.1 and 0.2 give 0.30000000000000004).
- gross_receipts: Whenever amounts are text, a number in the text is used ('100' and '250.5' give 350.5; '12x' counts as 12; '1e2' counts as 100.0); text with no leading number counts as 0 and adds nothing.
- gross_receipts: Whenever it is used with GROUP BY, each group is totalled separately by the same rules (a group with only refunds gives 0), and rows removed by WHERE are not counted.
- gross_receipts: Whenever DISTINCT is written inside it, it is ignored and every row is still added (amounts 5, 5, 3 give 13, not 8).
- slugify: Whenever a title is given, it returns the text in lower case with every run of characters that are not letters a-z or digits 0-9 (spaces, punctuation, tabs, line breaks, underscores, symbols) replaced by one single dash ('Hello, World!' gives 'hello-world'; 'snake_case' gives 'snake-case').
- slugify: Whenever the result would begin or end with a dash (leading or trailing spaces or punctuation, such as '  Hello   World  ' or '--Hello--'), those dashes are removed.
- slugify: Whenever the title has accented letters, they are reduced to the plain letter ('Café Crème Brûlée' gives 'cafe-creme-brulee'; 'Ça va' gives 'ca-va'), and full-width letters and digits, ligatures and superscripts are also converted to plain ones ('ﬁne' gives 'fine', 'x²' gives 'x2').
- slugify: Whenever a letter has no plain-letter form (ß, Æ, Ø, and all non-Latin scripts such as Japanese, and emoji), it is silently deleted rather than turned into a dash or transliterated ('Straße' gives 'strae'; 'Ærø Øl ß' gives 'r-l'; '日本語 Tokyo' gives 'tokyo').
- slugify: Whenever the title has typographic dashes or quotes (en dash, em dash, curly quotes), they are deleted and not turned into a dash, so the words either side are joined ('a–b—c' gives 'abc'). A plain apostrophe is also deleted, not turned into a dash ('dog's' gives 'dogs').
- slugify: Whenever the title has no letters or digits at all (empty, spaces only, '!!!', or only non-Latin characters), it returns 'untitled', not NULL and not empty text.
- slugify: Whenever the title is NULL, it returns NULL.
- slugify: Whenever the input is a number (12345 or 12.5), it is treated as its text and a decimal point becomes a dash ('12-5').
- mask_card: Whenever a card number has more than 4 digits, it returns one '*' for every digit except the last 4, followed by those last 4 digits ('4111 1111 1111 1111' gives '************1111'), so the result is as long as the number of digits.
- mask_card: Spaces and hyphens in the number stay exactly where they are, and the digits are masked as before, so that only the last four digits are shown and every other digit is replaced with '*' ('4111-1111-1111-1111' gives '****-****-****-1111'). Any other non-digit character, such as dots, slashes, underscores or brackets, makes it return 'INVALID'.
- mask_card: Whenever the number has 4 or fewer digits, every digit is masked, with one '*' per digit ('1234' gives '****'; '123' gives '***'; '0000' gives '****'), so the last 4 digits are not shown.
- mask_card: Whenever the input has no digits at all (empty text or just letters such as 'abcd'), it returns empty text.
- mask_card: Whenever the input is NULL, it returns NULL.
- mask_card: Whenever the input has letters or other text mixed with digits, only the digits count, and the last 4 digits found are shown even if they come from other text ('4111 1111 1111 1111 exp 12/26' gives '****************1226'; 'XXXX-XXXX-XXXX-1111' gives '****', because the X's and any existing '*' are dropped and only 4 digits remain).
- mask_card: Whenever the input is a plain number rather than text (4111111111111111), it is treated as its digits and masked in the same way; a number with a decimal point such as 41.5 counts its digits and not the point (3 digits give '***').
- mask_card: Whenever digits are written in non-Western numerals (such as Arabic-Indic digits), they are counted as digits and the last four are shown as written.
- Nothing else. Enter

## CB
There is no product owner to ask on this project: `tools/ask.py` will tell you so.

### The owner's rules for this feature (from his interview)
The owner decided each of these himself. Encode every one that touches your area as a test before you land, follow it exactly, and do not stretch it beyond the situation it describes.

- biz_days_between: Whenever two valid dates are given, it counts the Monday-to-Friday days from the start date up to but not including the end date, so the start day counts if it is a weekday and the end day never counts (Monday 2024-01-01 to Monday 2024-01-08 gives 5; Friday to the next Monday gives 1).
- biz_days_between: Whenever the start and end dates are the same day, it returns 0.
- biz_days_between: Whenever the end date is earlier than the start date, it counts the weekdays in the same way between the two dates and returns the result as a negative number (2024-01-08 back to 2024-01-01 gives -5).
- biz_days_between: Whenever the period contains only Saturdays and Sundays, it returns 0; a weekend start day is not counted but a weekend end day is simply excluded like any end day.
- biz_days_between: Saturdays and Sundays are skipped, and Jan 1 and Dec 25 are non-working days. No other holidays count; all other public holidays are counted as ordinary working days.
- biz_days_between: Whenever either date is NULL, it returns NULL.
- biz_days_between: Whenever either date is empty text, unreadable text (such as 'abc'), a number such as 2024, or a non-existent calendar date (such as 2024-02-30 or month 13), it returns NULL rather than an error or 0.
- biz_days_between: Whenever a date is written with a time after it (such as '2024-01-01 10:00:00' or '2024-01-01T09:00'), the time is ignored and only the first 10 characters are used as the date.
- biz_days_between: Whenever a date has extra text after its first 10 characters (such as '2024-01-10abc'), the extra text is ignored and the date is accepted; spaces around the date are also ignored.
- biz_days_between: Whenever a date is written with slashes ('2024/01/10'), without zero padding ('2024-1-10') or with a one-digit day ('2024-01-1'), it returns NULL; compact digits ('20240110') and ISO week dates ('2024-W01-1') are however accepted as valid dates, as is the number 20240110.
- fmt_phone: Whenever the text contains exactly 10 digits after ignoring everything that is not a digit, it returns the number as (AAA) BBB-CCCC, whatever the separators were (dashes, dots, spaces, brackets, plus sign).
- fmt_phone: Whenever the text contains exactly 11 digits and the first digit is 1, it drops that leading 1 and formats the remaining 10 digits as (AAA) BBB-CCCC (so '+1 555 123 4567' and '15551234567' both give '(555) 123-4567').
- fmt_phone: Whenever the text does not end up with exactly 10 digits, it returns an empty string instead of the original text. This covers 11 digits that do not start with 1 (such as '2 555 123 4567'), fewer than 10 digits, 12 or more digits, and an international number like '+44 20 7946 0958'. An extension like 'ext 89' is not counted as part of the 10 digits. When the number itself is valid, the extension is appended to it as ' x89'.
- fmt_phone: Whenever letters or other words are mixed in with exactly 10 digits (such as 'CALL-555-123-4567'), the non-digit characters are thrown away and the number is formatted; but a vanity number with letters instead of digits ('1-800-FLOWERS') has too few digits and is returned unchanged.
- fmt_phone: Whenever the area code or exchange begins with 0 or 1 (such as '0551234567'), it is still formatted as-is ('(055) 123-4567'); no check is made that the number is a valid North American number. Only a single leading 1 on an 11-digit number is removed.
- fmt_phone: Whenever the input is NULL, it returns NULL; whenever it is empty text, it returns empty text; whenever it has no digits ('abc'), it returns the text unchanged.
- fmt_phone: Whenever the input is a plain number rather than text (such as 5551234567 or 15551234567), it is treated as its digits and formatted; a decimal number such as 5551234567.0 is returned as the text '5551234567.0' because the extra digit makes 11 digits not starting with 1.
- fmt_phone: Whenever the digits are written in non-Western numerals (such as Arabic-Indic digits), they are not recognised as digits and the text is returned unchanged.
- grade_letter: Whenever the score is 92 or more it returns 'A'; 83 or more but under 92 returns 'B'; 71 or more but under 83 returns 'C'; 60 or more but under 71 returns 'D'; anything lower returns 'F'.
- grade_letter: Whenever the score is exactly on a boundary (90, 80, 70, 60) it gets the higher grade; scores are never rounded, so 89.99 or 89.9999999 is a 'B' and 59.99 is an 'F'.
- grade_letter: Whenever the score is above 100 or below 0 it returns 'X'. Exactly 0 is valid and returns 'F'. Exactly 100 is valid and returns 'A'.
- grade_letter: Whenever the score is NULL, it returns NULL.
- grade_letter: Whenever the score is text holding a number ('95', ' 85 ', '89.5', '1e2'), it is read as that number; text that starts with a number ('85%', '90abc') uses the leading number.
- grade_letter: Whenever the score is empty text, text with no leading number ('abc', 'A', '-', '0x5A'), or the boolean true, it is treated as 0 and returns 'F' rather than NULL.
- late_fee: Whenever an invoice is late by a positive number of days, the first 5 days late are free, so only the days beyond the 5th are charged. An invoice late by 5 days or fewer has no fee. For each charged day the fee is 0.5% of the invoice amount in cents, and the total is rounded down to a whole number of cents. The fee has a minimum of 500 cents, and it is capped at 20% of the invoice amount in cents, rounded down. The cap wins over the minimum, so on a small invoice where 20% of the invoice is less than 500 cents, the fee is that 20% amount. Example: 10000 cents, 10 days late: 5 charged days give 250, raised to the 500 minimum, so the fee is 500. The cap here is 2000.
- late_fee: Whenever the fee is not a whole number of cents, it is rounded to the nearest cent with exact halves rounded up (100 cents for 3 days gives 2; 1 cent for 100 days gives 1; 1 cent for 99 days gives 0; 99 cents for 10 days gives 5).
- late_fee: Whenever days late is zero or negative (not late), or the invoice amount is zero or negative, the fee is 0.
- late_fee: Whenever either the amount or the days late is NULL, it returns NULL.
- late_fee: Whenever days late is a fraction (such as 1.5) it is used as is in the calculation (10000 cents for 1.5 days gives 75), and a fractional amount (1000.5) is used as is before the final rounding to a whole cent.
- late_fee: Whenever the amount or days late is text, a number in the text is used ('10000' and '10' give 500; '3 days' counts as 3); empty text or text with no leading number counts as 0, so the fee is 0 and not NULL.
- shipping_cost: Whenever the weight and zone are valid, the charge is zone x (300 + 100 x the number of started kilograms) cents, where any part of a kilogram counts as a whole one (500 g in zone 1 gives 400; exactly 1000 g gives 400; 1001 g gives 500; 2500 g in zone 2 gives 1200).
- shipping_cost: Whenever the weight is exactly 0, the charge is the base amount only: zone x 300 cents (zone 3 gives 900), and the fractional weight 0.5 g counts as one started kilogram.
- shipping_cost: Whenever the weight is negative, it returns NULL.
- shipping_cost: A zone that is not a number at all (empty text, 'abc', 'A'), is not a whole number (1.5), or is outside 1 to 3 (below 1, meaning zero or negative, or above 3) is billed as zone 3, and it does not return NULL. A whole-valued zone like 2.0 or '1.0' is accepted as that zone number. There is no zone above 3, so zone 100 is billed as zone 3.
- shipping_cost: Whenever the weight or zone is NULL, it returns NULL.
- shipping_cost: Whenever the weight is text, a number in the text is used ('500', '2kg' counts as 2 g); empty text or text with no leading number counts as a weight of 0 (charged only the base amount), while text with a leading number in the zone ('2z' is zone 2) is accepted.
- shipping_cost: Whenever the weight is over 30000 g, the charge is a flat 9999, whatever the zone (for example, 1,000,000,000 g in zone 1 gives 9999). A weight of exactly 30000 g is priced normally.
- tiered_price: Whenever the quantity is under 10, the total is the unit price times the quantity with no discount (250 cents x 5 gives 1250).
- tiered_price: Whenever the quantity is 10 to 49 units, the whole order, not just the units above 10, gets 10% off (250 x 10 gives 2250; 250 x 11 gives 2475), so 10 units can cost the same as 9 units (2250 each). Whenever the quantity is 50 or more, the whole order gets 20% off.
- tiered_price: The total is rounded to the nearest 5 cents, with exact halves rounded up, so the total is always a multiple of 5 cents (1 cent x 10 gives 10; 1 cent x 15 gives 15; 1 cent x 25 gives 25; 99.5 cents x 3 gives 300).
- tiered_price: Whenever the quantity is 0 or the unit price is 0, the total is 0.
- tiered_price: Whenever the unit price or quantity is negative, it returns NULL.
- tiered_price: Whenever either the unit price or quantity is NULL, it returns NULL.
- tiered_price: Whenever the quantity is a fraction, it is used as is and the discount applies only when it is 10 or more (9.99 gives no discount, 250 x 9.99 gives 2498; 10.0 gets the discount).
- tiered_price: Whenever the price or quantity is text, a number in the text is used ('250' and '10' give 2250; '12x' counts as 12); empty text or text with no leading number counts as 0, so the total is 0 and not NULL.
- weighted_rating: Whenever the rating and the number of votes are valid, the result is (votes x average rating + 30) / (votes + 10), that is the average pulled toward a neutral prior of 3.0 that is worth 10 votes (5.0 with 10 votes gives 4.0; 4.5 with 100 votes gives 4.36).
- weighted_rating: Whenever the result is calculated, it is rounded to 2 decimal places with exact halves rounded up, and is returned as a decimal number (4.0, not 4).
- weighted_rating: Whenever there are fewer than 5 votes, including 0 votes, the result is NULL. Exactly 5 votes is accepted.
- weighted_rating: Whenever the votes are negative, it returns NULL; whenever either the rating or the votes are NULL, it returns NULL.
- weighted_rating: Whenever the average rating lies outside any normal scale (0, negative or above 5, such as -2 or 7), it is not rejected or limited and is used as given (rating 0 with 10 votes gives 1.5; rating 7 with 10 votes gives 5.0).
- weighted_rating: Whenever the votes are a fraction (2.5), they are used as is in the calculation.
- weighted_rating: Whenever the rating or votes are text, a number in the text is used ('5' and '10' give 4.0); empty text or text with no leading number counts as 0, so a rating of 'abc' counts as rating 0 (giving 1.5 with 10 votes) and votes of 'abc' counts as 0 votes (giving 3.0).
- gross_receipts: Whenever a group of rows is totalled, it adds up only the amounts that are greater than zero; negative amounts (refunds) are left out and not subtracted (100, -50, 300 gives 400).
- gross_receipts: Whenever an amount is NULL or exactly 0, it adds nothing to the total.
- gross_receipts: Whenever there are no rows, only NULL amounts, or only zero or negative amounts, the total is 0, not NULL. Correction from the owner, which overrides anything above that it contradicts: It should return NULL, not 0, when there are no valid rows.
- gross_receipts: Whenever every counted amount is a whole number, the total is a whole number; whenever any counted amount has decimals the total is a decimal number (100.5 and 200 give 300.5), using ordinary floating point addition (0.1 and 0.2 give 0.30000000000000004).
- gross_receipts: Whenever amounts are text, a number in the text is used ('100' and '250.5' give 350.5; '12x' counts as 12; '1e2' counts as 100.0); text with no leading number counts as 0 and adds nothing.
- gross_receipts: Whenever it is used with GROUP BY, each group is totalled separately by the same rules (a group with only refunds gives 0), and rows removed by WHERE are not counted.
- gross_receipts: Whenever DISTINCT is written inside it, it is ignored and every row is still added (amounts 5, 5, 3 give 13, not 8).
- slugify: Whenever a title is given, it returns the text in lower case with every run of characters that are not letters a-z or digits 0-9 (spaces, punctuation, tabs, line breaks, underscores, symbols) replaced by one single dash ('Hello, World!' gives 'hello-world'; 'snake_case' gives 'snake-case').
- slugify: Whenever the result would begin or end with a dash (leading or trailing spaces or punctuation, such as '  Hello   World  ' or '--Hello--'), those dashes are removed.
- slugify: Whenever the title has accented letters, they are reduced to the plain letter ('Café Crème Brûlée' gives 'cafe-creme-brulee'; 'Ça va' gives 'ca-va'), and full-width letters and digits, ligatures and superscripts are also converted to plain ones ('ﬁne' gives 'fine', 'x²' gives 'x2').
- slugify: Whenever a letter has no plain-letter form (ß, Æ, Ø, and all non-Latin scripts such as Japanese, and emoji), it is silently deleted rather than turned into a dash or transliterated ('Straße' gives 'strae'; 'Ærø Øl ß' gives 'r-l'; '日本語 Tokyo' gives 'tokyo').
- slugify: Whenever the title has typographic dashes or quotes (en dash, em dash, curly quotes), they are deleted and not turned into a dash, so the words either side are joined ('a–b—c' gives 'abc'). A plain apostrophe is also deleted, not turned into a dash ('dog's' gives 'dogs').
- slugify: Whenever the title has no letters or digits at all (empty, spaces only, '!!!', or only non-Latin characters), it returns 'untitled', not NULL and not empty text.
- slugify: Whenever the title is NULL, it returns NULL.
- slugify: Whenever the input is a number (12345 or 12.5), it is treated as its text and a decimal point becomes a dash ('12-5').
- mask_card: Whenever a card number has more than 4 digits, it returns one '*' for every digit except the last 4, followed by those last 4 digits ('4111 1111 1111 1111' gives '************1111'), so the result is as long as the number of digits.
- mask_card: Spaces and hyphens in the number stay exactly where they are, and the digits are masked as before, so that only the last four digits are shown and every other digit is replaced with '*' ('4111-1111-1111-1111' gives '****-****-****-1111'). Any other non-digit character, such as dots, slashes, underscores or brackets, makes it return 'INVALID'.
- mask_card: Whenever the number has 4 or fewer digits, every digit is masked, with one '*' per digit ('1234' gives '****'; '123' gives '***'; '0000' gives '****'), so the last 4 digits are not shown.
- mask_card: Whenever the input has no digits at all (empty text or just letters such as 'abcd'), it returns empty text.
- mask_card: Whenever the input is NULL, it returns NULL.
- mask_card: Whenever the input has letters or other text mixed with digits, only the digits count, and the last 4 digits found are shown even if they come from other text ('4111 1111 1111 1111 exp 12/26' gives '****************1226'; 'XXXX-XXXX-XXXX-1111' gives '****', because the X's and any existing '*' are dropped and only 4 digits remain).
- mask_card: Whenever the input is a plain number rather than text (4111111111111111), it is treated as its digits and masked in the same way; a number with a decimal point such as 41.5 counts its digits and not the point (3 digits give '***').
- mask_card: Whenever digits are written in non-Western numerals (such as Arabic-Indic digits), they are counted as digits and the last four are shown as written.
- Nothing else. Enter

## DG
There is no product owner to ask on this project: `tools/ask.py` will tell you so.

### The owner's rules for this feature (from his interview)
The owner decided each of these himself. Encode every one that touches your area as a test before you land, follow it exactly, and do not stretch it beyond the situation it describes.

- biz_days_between: Whenever two valid dates are given, it counts the Monday-to-Friday days from the start date up to but not including the end date, so the start day counts if it is a weekday and the end day never counts (Monday 2024-01-01 to Monday 2024-01-08 gives 5; Friday to the next Monday gives 1).
- biz_days_between: Whenever the start and end dates are the same day, it returns 0.
- biz_days_between: Whenever the end date is earlier than the start date, it counts the weekdays in the same way between the two dates and returns the result as a negative number (2024-01-08 back to 2024-01-01 gives -5).
- biz_days_between: Whenever the period contains only Saturdays and Sundays, it returns 0; a weekend start day is not counted but a weekend end day is simply excluded like any end day.
- biz_days_between: Saturdays and Sundays are skipped, and Jan 1 and Dec 25 are non-working days. No other holidays count; all other public holidays are counted as ordinary working days.
- biz_days_between: Whenever either date is NULL, it returns NULL.
- biz_days_between: Whenever either date is empty text, unreadable text (such as 'abc'), a number such as 2024, or a non-existent calendar date (such as 2024-02-30 or month 13), it returns NULL rather than an error or 0.
- biz_days_between: Whenever a date is written with a time after it (such as '2024-01-01 10:00:00' or '2024-01-01T09:00'), the time is ignored and only the first 10 characters are used as the date.
- biz_days_between: Whenever a date has extra text after its first 10 characters (such as '2024-01-10abc'), the extra text is ignored and the date is accepted; spaces around the date are also ignored.
- biz_days_between: Whenever a date is written with slashes ('2024/01/10'), without zero padding ('2024-1-10') or with a one-digit day ('2024-01-1'), it returns NULL; compact digits ('20240110') and ISO week dates ('2024-W01-1') are however accepted as valid dates, as is the number 20240110.
- fmt_phone: Whenever the text contains exactly 10 digits after ignoring everything that is not a digit, it returns the number as (AAA) BBB-CCCC, whatever the separators were (dashes, dots, spaces, brackets, plus sign).
- fmt_phone: Whenever the text contains exactly 11 digits and the first digit is 1, it drops that leading 1 and formats the remaining 10 digits as (AAA) BBB-CCCC (so '+1 555 123 4567' and '15551234567' both give '(555) 123-4567').
- fmt_phone: Whenever the text does not end up with exactly 10 digits, it returns an empty string instead of the original text. This covers 11 digits that do not start with 1 (such as '2 555 123 4567'), fewer than 10 digits, 12 or more digits, and an international number like '+44 20 7946 0958'. An extension like 'ext 89' is not counted as part of the 10 digits. When the number itself is valid, the extension is appended to it as ' x89'.
- fmt_phone: Whenever letters or other words are mixed in with exactly 10 digits (such as 'CALL-555-123-4567'), the non-digit characters are thrown away and the number is formatted; but a vanity number with letters instead of digits ('1-800-FLOWERS') has too few digits and is returned unchanged.
- fmt_phone: Whenever the area code or exchange begins with 0 or 1 (such as '0551234567'), it is still formatted as-is ('(055) 123-4567'); no check is made that the number is a valid North American number. Only a single leading 1 on an 11-digit number is removed.
- fmt_phone: Whenever the input is NULL, it returns NULL; whenever it is empty text, it returns empty text; whenever it has no digits ('abc'), it returns the text unchanged.
- fmt_phone: Whenever the input is a plain number rather than text (such as 5551234567 or 15551234567), it is treated as its digits and formatted; a decimal number such as 5551234567.0 is returned as the text '5551234567.0' because the extra digit makes 11 digits not starting with 1.
- fmt_phone: Whenever the digits are written in non-Western numerals (such as Arabic-Indic digits), they are not recognised as digits and the text is returned unchanged.
- grade_letter: Whenever the score is 92 or more it returns 'A'; 83 or more but under 92 returns 'B'; 71 or more but under 83 returns 'C'; 60 or more but under 71 returns 'D'; anything lower returns 'F'.
- grade_letter: Whenever the score is exactly on a boundary (90, 80, 70, 60) it gets the higher grade; scores are never rounded, so 89.99 or 89.9999999 is a 'B' and 59.99 is an 'F'.
- grade_letter: Whenever the score is above 100 or below 0 it returns 'X'. Exactly 0 is valid and returns 'F'. Exactly 100 is valid and returns 'A'.
- grade_letter: Whenever the score is NULL, it returns NULL.
- grade_letter: Whenever the score is text holding a number ('95', ' 85 ', '89.5', '1e2'), it is read as that number; text that starts with a number ('85%', '90abc') uses the leading number.
- grade_letter: Whenever the score is empty text, text with no leading number ('abc', 'A', '-', '0x5A'), or the boolean true, it is treated as 0 and returns 'F' rather than NULL.
- late_fee: Whenever an invoice is late by a positive number of days, the first 5 days late are free, so only the days beyond the 5th are charged. An invoice late by 5 days or fewer has no fee. For each charged day the fee is 0.5% of the invoice amount in cents, and the total is rounded down to a whole number of cents. The fee has a minimum of 500 cents, and it is capped at 20% of the invoice amount in cents, rounded down. The cap wins over the minimum, so on a small invoice where 20% of the invoice is less than 500 cents, the fee is that 20% amount. Example: 10000 cents, 10 days late: 5 charged days give 250, raised to the 500 minimum, so the fee is 500. The cap here is 2000.
- late_fee: Whenever the fee is not a whole number of cents, it is rounded to the nearest cent with exact halves rounded up (100 cents for 3 days gives 2; 1 cent for 100 days gives 1; 1 cent for 99 days gives 0; 99 cents for 10 days gives 5).
- late_fee: Whenever days late is zero or negative (not late), or the invoice amount is zero or negative, the fee is 0.
- late_fee: Whenever either the amount or the days late is NULL, it returns NULL.
- late_fee: Whenever days late is a fraction (such as 1.5) it is used as is in the calculation (10000 cents for 1.5 days gives 75), and a fractional amount (1000.5) is used as is before the final rounding to a whole cent.
- late_fee: Whenever the amount or days late is text, a number in the text is used ('10000' and '10' give 500; '3 days' counts as 3); empty text or text with no leading number counts as 0, so the fee is 0 and not NULL.
- shipping_cost: Whenever the weight and zone are valid, the charge is zone x (300 + 100 x the number of started kilograms) cents, where any part of a kilogram counts as a whole one (500 g in zone 1 gives 400; exactly 1000 g gives 400; 1001 g gives 500; 2500 g in zone 2 gives 1200).
- shipping_cost: Whenever the weight is exactly 0, the charge is the base amount only: zone x 300 cents (zone 3 gives 900), and the fractional weight 0.5 g counts as one started kilogram.
- shipping_cost: Whenever the weight is negative, it returns NULL.
- shipping_cost: A zone that is not a number at all (empty text, 'abc', 'A'), is not a whole number (1.5), or is outside 1 to 3 (below 1, meaning zero or negative, or above 3) is billed as zone 3, and it does not return NULL. A whole-valued zone like 2.0 or '1.0' is accepted as that zone number. There is no zone above 3, so zone 100 is billed as zone 3.
- shipping_cost: Whenever the weight or zone is NULL, it returns NULL.
- shipping_cost: Whenever the weight is text, a number in the text is used ('500', '2kg' counts as 2 g); empty text or text with no leading number counts as a weight of 0 (charged only the base amount), while text with a leading number in the zone ('2z' is zone 2) is accepted.
- shipping_cost: Whenever the weight is over 30000 g, the charge is a flat 9999, whatever the zone (for example, 1,000,000,000 g in zone 1 gives 9999). A weight of exactly 30000 g is priced normally.
- tiered_price: Whenever the quantity is under 10, the total is the unit price times the quantity with no discount (250 cents x 5 gives 1250).
- tiered_price: Whenever the quantity is 10 to 49 units, the whole order, not just the units above 10, gets 10% off (250 x 10 gives 2250; 250 x 11 gives 2475), so 10 units can cost the same as 9 units (2250 each). Whenever the quantity is 50 or more, the whole order gets 20% off.
- tiered_price: The total is rounded to the nearest 5 cents, with exact halves rounded up, so the total is always a multiple of 5 cents (1 cent x 10 gives 10; 1 cent x 15 gives 15; 1 cent x 25 gives 25; 99.5 cents x 3 gives 300).
- tiered_price: Whenever the quantity is 0 or the unit price is 0, the total is 0.
- tiered_price: Whenever the unit price or quantity is negative, it returns NULL.
- tiered_price: Whenever either the unit price or quantity is NULL, it returns NULL.
- tiered_price: Whenever the quantity is a fraction, it is used as is and the discount applies only when it is 10 or more (9.99 gives no discount, 250 x 9.99 gives 2498; 10.0 gets the discount).
- tiered_price: Whenever the price or quantity is text, a number in the text is used ('250' and '10' give 2250; '12x' counts as 12); empty text or text with no leading number counts as 0, so the total is 0 and not NULL.
- weighted_rating: Whenever the rating and the number of votes are valid, the result is (votes x average rating + 30) / (votes + 10), that is the average pulled toward a neutral prior of 3.0 that is worth 10 votes (5.0 with 10 votes gives 4.0; 4.5 with 100 votes gives 4.36).
- weighted_rating: Whenever the result is calculated, it is rounded to 2 decimal places with exact halves rounded up, and is returned as a decimal number (4.0, not 4).
- weighted_rating: Whenever there are fewer than 5 votes, including 0 votes, the result is NULL. Exactly 5 votes is accepted.
- weighted_rating: Whenever the votes are negative, it returns NULL; whenever either the rating or the votes are NULL, it returns NULL.
- weighted_rating: Whenever the average rating lies outside any normal scale (0, negative or above 5, such as -2 or 7), it is not rejected or limited and is used as given (rating 0 with 10 votes gives 1.5; rating 7 with 10 votes gives 5.0).
- weighted_rating: Whenever the votes are a fraction (2.5), they are used as is in the calculation.
- weighted_rating: Whenever the rating or votes are text, a number in the text is used ('5' and '10' give 4.0); empty text or text with no leading number counts as 0, so a rating of 'abc' counts as rating 0 (giving 1.5 with 10 votes) and votes of 'abc' counts as 0 votes (giving 3.0).
- gross_receipts: Whenever a group of rows is totalled, it adds up only the amounts that are greater than zero; negative amounts (refunds) are left out and not subtracted (100, -50, 300 gives 400).
- gross_receipts: Whenever an amount is NULL or exactly 0, it adds nothing to the total.
- gross_receipts: Whenever there are no rows, only NULL amounts, or only zero or negative amounts, the total is 0, not NULL. Correction from the owner, which overrides anything above that it contradicts: It should return NULL, not 0, when there are no valid rows.
- gross_receipts: Whenever every counted amount is a whole number, the total is a whole number; whenever any counted amount has decimals the total is a decimal number (100.5 and 200 give 300.5), using ordinary floating point addition (0.1 and 0.2 give 0.30000000000000004).
- gross_receipts: Whenever amounts are text, a number in the text is used ('100' and '250.5' give 350.5; '12x' counts as 12; '1e2' counts as 100.0); text with no leading number counts as 0 and adds nothing.
- gross_receipts: Whenever it is used with GROUP BY, each group is totalled separately by the same rules (a group with only refunds gives 0), and rows removed by WHERE are not counted.
- gross_receipts: Whenever DISTINCT is written inside it, it is ignored and every row is still added (amounts 5, 5, 3 give 13, not 8).
- slugify: Whenever a title is given, it returns the text in lower case with every run of characters that are not letters a-z or digits 0-9 (spaces, punctuation, tabs, line breaks, underscores, symbols) replaced by one single dash ('Hello, World!' gives 'hello-world'; 'snake_case' gives 'snake-case').
- slugify: Whenever the result would begin or end with a dash (leading or trailing spaces or punctuation, such as '  Hello   World  ' or '--Hello--'), those dashes are removed.
- slugify: Whenever the title has accented letters, they are reduced to the plain letter ('Café Crème Brûlée' gives 'cafe-creme-brulee'; 'Ça va' gives 'ca-va'), and full-width letters and digits, ligatures and superscripts are also converted to plain ones ('ﬁne' gives 'fine', 'x²' gives 'x2').
- slugify: Whenever a letter has no plain-letter form (ß, Æ, Ø, and all non-Latin scripts such as Japanese, and emoji), it is silently deleted rather than turned into a dash or transliterated ('Straße' gives 'strae'; 'Ærø Øl ß' gives 'r-l'; '日本語 Tokyo' gives 'tokyo').
- slugify: Whenever the title has typographic dashes or quotes (en dash, em dash, curly quotes), they are deleted and not turned into a dash, so the words either side are joined ('a–b—c' gives 'abc'). A plain apostrophe is also deleted, not turned into a dash ('dog's' gives 'dogs').
- slugify: Whenever the title has no letters or digits at all (empty, spaces only, '!!!', or only non-Latin characters), it returns 'untitled', not NULL and not empty text.
- slugify: Whenever the title is NULL, it returns NULL.
- slugify: Whenever the input is a number (12345 or 12.5), it is treated as its text and a decimal point becomes a dash ('12-5').
- mask_card: Whenever a card number has more than 4 digits, it returns one '*' for every digit except the last 4, followed by those last 4 digits ('4111 1111 1111 1111' gives '************1111'), so the result is as long as the number of digits.
- mask_card: Spaces and hyphens in the number stay exactly where they are, and the digits are masked as before, so that only the last four digits are shown and every other digit is replaced with '*' ('4111-1111-1111-1111' gives '****-****-****-1111'). Any other non-digit character, such as dots, slashes, underscores or brackets, makes it return 'INVALID'.
- mask_card: Whenever the number has 4 or fewer digits, every digit is masked, with one '*' per digit ('1234' gives '****'; '123' gives '***'; '0000' gives '****'), so the last 4 digits are not shown.
- mask_card: Whenever the input has no digits at all (empty text or just letters such as 'abcd'), it returns empty text.
- mask_card: Whenever the input is NULL, it returns NULL.
- mask_card: Whenever the input has letters or other text mixed with digits, only the digits count, and the last 4 digits found are shown even if they come from other text ('4111 1111 1111 1111 exp 12/26' gives '****************1226'; 'XXXX-XXXX-XXXX-1111' gives '****', because the X's and any existing '*' are dropped and only 4 digits remain).
- mask_card: Whenever the input is a plain number rather than text (4111111111111111), it is treated as its digits and masked in the same way; a number with a decimal point such as 41.5 counts its digits and not the point (3 digits give '***').
- mask_card: Whenever digits are written in non-Western numerals (such as Arabic-Indic digits), they are counted as digits and the last four are shown as written.
- Nothing else. Enter
