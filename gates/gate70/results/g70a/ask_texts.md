# Gate 55 ask texts (gates/gate55/referee/review55.py)

## N0
There is no product owner to ask on this project: `tools/ask.py` will tell you so. Work from the spec and the examples.

## QN
The product owner is away until the morning. For every business decision a function's one-line spec leaves open (cut-offs and boundaries, rounding, minimums and caps, what happens with blank, missing, negative or oddly formatted input), record one question for him with `python3 /home/claude/hive/gates/gate70/referee/queue_question.py /home/claude/hive/runs/g70a/queue_QN.jsonl "<your question>"`, in plain business words, one decision per question; he will answer them all in the morning. Then build your best guess and keep going. Do not record a question a teammate has already recorded (`cat /home/claude/hive/runs/g70a/queue_QN.jsonl`). (`tools/ask.py` is not used on this project.)

## HV
There is no product owner to ask on this project: `tools/ask.py` will tell you so.

### The owner's rules for this feature (from his interview)
The owner decided each of these himself. Encode every one that touches your area as a test before you land, follow it exactly, and do not stretch it beyond the situation it describes.

- Whenever age_years is given a birth date and an as-of date, it returns the number of whole years completed, counting a birthday as reached on the same month and day of the as-of year (e.g. born 1990-05-15, as of 2024-05-15 gives 34; one day earlier gives 33).
- Whenever age_years is asked about someone born on 29 February, the birthday is treated as reached on 1 March in non-leap years (born 2000-02-29 is 0 on 2001-02-28 and 1 on 2001-03-01) and on 29 February in leap years.
- Whenever age_years gets an as-of date equal to the birth date, it returns 0; whenever the as-of date is earlier than the birth date, it returns -1 (not NULL and not blank), however far earlier the as-of date is.
- Whenever either date given to age_years is NULL, empty, not a real calendar date (such as month 13), or not in the strict YYYY-MM-DD form (no slashes, no compact 20000101, no missing zero padding like 2000-1-1), age_years returns NULL.
- Whenever a date given to age_years has surrounding spaces, or has extra text after the first 10 characters (such as a time '2000-01-01 12:00:00' or even junk like '2000-01-01abc'), age_years ignores the spaces and the extra text and uses only the date part.
- Whenever a date given to age_years is a plain number such as 20000101, age_years returns NULL because it is not in YYYY-MM-DD form.
- Whenever biz_days is given a start and end date in order, it counts the Monday-to-Friday days from the start date up to but not including the end date (2024-01-01 to 2024-01-08 gives 5; 2024-01-01 to 2024-01-05 gives 4).
- Whenever the start date of biz_days is itself a weekday, that day is counted; whenever the end date is a weekday it is not counted (2024-01-05 Friday to 2024-01-06 gives 1; 2024-01-06 Saturday to 2024-01-08 gives 0).
- Whenever biz_days is given the same start and end date, it returns 0, whatever day of the week it is.
- Whenever the end date given to biz_days is earlier than the start date, it returns 0 (it never returns a negative number and does not give an error), whatever days of the week the dates fall on (2024-01-08 to 2024-01-01 gives 0; 2024-03-08 to 2024-03-04 gives 0).
- Whenever biz_days counts working days, it treats Saturday and Sunday as non-working. It also treats December 25 and January 1 of every year as non-working holidays. No other public holidays are excluded, and December 26 is a normal working day when it falls on a weekday (2024-12-24 to 2024-12-26 gives 2; 2024-12-23 to 2024-12-28 gives 4).
- Whenever either date given to biz_days is NULL, empty, not a real date, or not in strict YYYY-MM-DD form, biz_days returns NULL.
- Whenever a date given to biz_days has surrounding spaces or extra text after its first 10 characters (such as a time of day), biz_days ignores that and uses only the date part.
- Whenever grade_letter is given a score, it grades the score after rounding it to a whole number (see rule 15). A rounded score of 90 or more, up to and including 100, returns A (except that exactly 100 returns A+, see rule 15); 80 up to under 90 gives B; 70 up to under 80 gives C; 60 up to under 70 gives D; 0 up to under 60 gives F. A rounded score above 100 is never graded: it is INVALID (see rule 15), however high it is. A rounded score below 0 is never graded either: it is INVALID (see rule 15), however low it is, and it does not get an F. Each boundary score belongs to the higher grade, and the cut-offs apply to the rounded score, not the original one. So 90 is A, 89.99 rounds to 90 and is A, 89.4 rounds to 89 and is B, 60 is D, 59.6 rounds to 60 and is D, 59.4 rounds to 59 and is F, 0 is F, -0.4 rounds to 0 and is F, -5 is INVALID, not F, and 150 is INVALID, not A.
- grade_letter first rounds the score to a whole number. After rounding, a score above 100 or below 0 is INVALID, a score of exactly 100 returns A+, and a score of zero returns F.
- Whenever grade_letter is given a score as text that is entirely a number (such as '85', ' 85 ' with spaces, or '9e1'), it reads it as that number and grades it normally.
- Whenever grade_letter is given NULL, empty text, or text that is not wholly a number (such as 'abc' or '85abc'), it returns NULL rather than F.
- Whenever grade_letter is given the text 'inf' it treats it as infinitely high, which is above 100, so it returns INVALID (not A); whenever it is given the text '-inf' it treats it as infinitely low, which is below 0, so it returns INVALID (not F); and whenever it is given the text 'nan' it returns NULL.
- Whenever late_fee is given an overdue amount in cents and days late of 5 or fewer, it returns 0 because the first 5 days are a grace period. Past 5 days late, the fee is 1% of the amount per late week (rounded up). The minimum of 500 cents always applies to any fee charged past the grace period: if the 1%-per-week figure is less than 500 cents, the fee is raised to 500 cents (for example, 10000 cents that is 8 days late gives 2 weeks, which is 200 cents, so the fee is 500 cents). The fee is also capped at 25% of the amount.
- The 2%, 5% and 9% late_fee bands (8 to 14 days, 15 to 30 days, and 31 or more days late) are dropped and never apply, however many days late. For any days late past the 5-day grace period, late_fee charges only the 1%-per-late-week fee from rule 19, with the same rounding, 500-cent minimum and 25% cap. For example, 100 rupees (10000 cents) is 5 rupees (500 cents) at 30 days late and still 5 rupees at 31 days late, because both are 5 late weeks, not 9%.
- Whenever late_fee computes the percentage part of a fee, it rounds to a whole cent with halves rounding up (a fee of 20.5 cents becomes 21; 0.5 cents becomes 1; 0.48 cents becomes 0). This rounding is done on the percentage figure before the 500-cent minimum and the 25% cap are applied, so a rounded figure below 500 cents, including 0, is still raised to the minimum whenever the days late are past the grace period.
- Whenever late_fee is given an amount of exactly zero, or days late that are negative or zero, it returns 0. Whenever the amount is negative (a credit) and days late are past the 5-day grace period (more than 5, fractions included), the fee is the negative cap: 25% of the amount, so it is also negative (for example, -10000 cents that is 31 days late gives -2500 cents, which is -25 rupees). For a negative amount the 1%-per-late-week fee, the 500-cent minimum and the percentage bands do not apply, and this fee is rounded to a whole cent with halves rounding up, as in rule 21. A negative amount with 5 or fewer days late is still within the grace period and returns 0, as in rule 19. Positive amounts are not affected by this rule.
- Whenever days late given to late_fee is a fraction, the exact value is used, and any part of a week counts as a whole late week (14.5 days is past the 5-day grace period and counts as 3 late weeks, because 14.5 divided by 7 is a little over 2 and is rounded up). The fee is the usual 1% of the amount per late week, with no percentage bands. A fractional amount is used as given before rounding.
- Whenever either amount or days late given to late_fee is NULL, empty text, or text that is not wholly a number, it returns NULL, even if the other value would have given 0; numeric text such as '10000' and '20' is read as a number.
- Whenever loyalty_pts is given a purchase amount in cents and a tier, it awards whole points based on 1 point per 100 cents for basic, 1.5 for silver, 2 for gold and 3 for platinum, rounding down any fraction of a point (10000 cents gives 100, 150, 200 and 300 points respectively; 99 cents basic gives 0, 199 cents gold gives 3).
- Whenever the tier given to loyalty_pts is missing (NULL) or is not one of basic, silver, gold or platinum (such as 'bronze', an empty text, or a number), it is treated as basic and earns 1 point per 100 cents (for example, a missing tier on 10000 cents gives 100 points).
- Whenever the tier given to loyalty_pts is written in any letter case or with spaces around it (' GOLD ', 'Gold'), it is recognised as that tier; spaces inside a name (such as 'bro nze') stop it matching and it counts as basic.
- Whenever the amount given to loyalty_pts is zero, it returns 0 points. Whenever the amount is negative (a return or refund), it returns negative points: the points taken back are the same as the points the matching positive amount would earn for that tier, using the same rates, the same tier rules and the same rounding down of any fraction of a point, then shown as a negative number (for example, -5000 cents for gold gives -100, and -99 cents for basic gives 0).
- Whenever the amount given to loyalty_pts is text that is not a number (such as 'abc' or empty text), it is treated as zero and returns 0 points; numeric text such as '5000' is read as a number.
- Whenever the amount given to loyalty_pts has a fraction (such as 5050.7 cents), the fraction counts in the calculation before rounding points down.
- Whenever the amount given to loyalty_pts is NULL, it returns NULL, even when the tier is given. A NULL tier does not make the result NULL: a missing tier is treated as basic (see rule 26), so a NULL tier with a given amount returns the basic-rate points, including 0 for a zero amount and negative points for a negative amount.
- Whenever mask_card is given text containing more than 4 digits, it replaces every digit except the last 4 digits with an asterisk, so 4111111111111111 becomes ************1111.
- Whenever mask_card is given a card number with spaces or dashes between groups, it keeps those separators and any other non-digit characters in place and masks only the digits (4111 1111 1111 1111 becomes **** **** **** 1111; 4111-1111-1111-1111 becomes ****-****-****-1111).
- Whenever the text given to mask_card contains no digits at all, it returns INVALID. This includes empty text (a blank card field, which must show INVALID and never come back as empty text), text made only of spaces, and text such as 'abcd'. Whenever the text contains 1 to 4 digits in total, every digit becomes '*' (for example 1234 returns ****, 123 returns ***, 12-34 returns **-**). Exactly 5 digits leaves only the first masked.
- Whenever mask_card is given text with other words and digits mixed (such as 'card 1234567890 ok'), it masks all digits in the whole text except the last 4 digits found anywhere in it, leaving letters untouched ('card ******7890 ok'; 'x1y2z3w4v5' becomes 'x*y2z3w4v5'). This keep-the-last-4 step applies only when the whole text has more than 4 digits in total. If the text has 1 to 4 digits in total, every digit is masked and none is shown, as in rule 34 ('card 1234 ok' becomes 'card **** ok').
- Whenever mask_card is given a number rather than text (such as 4111111111111111), it treats it as text of its digits and masks it the same way; a decimal such as 12345.5 counts all its digits and keeps the point ('**345.5').
- Whenever mask_card is given NULL it returns NULL.
- Whenever mask_card is given spaces around the number, it keeps them unchanged and does not count them as digits; it counts digits from other scripts and superscript digits as digits too and masks them in the same way.
- Whenever shift_pay is given hours worked up to 40 and an hourly rate in cents, it returns hours times the rate (40 hours at 1000 cents gives 40000; 39.5 hours gives 39500).
- Whenever shift_pay is given more than 40 hours, the first 40 hours are paid at the normal rate and each hour beyond 40 is paid at 1.5 times the rate (45 hours at 1000 cents gives 47500; 100 hours gives 130000), with no cap on hours.
- Whenever shift_pay computes pay that has a fraction of a cent, it rounds to a whole cent with halves rounding up (10.5 hours at 1001 cents is 10510.5 and gives 10511; 0.5 hours at 1 cent gives 1).
- Whenever the hours given to shift_pay is zero, or the rate given to it is zero or negative, it returns 0 rather than a negative pay. Whenever the hours are negative and the rate is positive, it returns a negative pay equal to hours times the rate, with no overtime rate (-5 hours at 2000 cents gives -10000 cents, which is -100 rupees).
- Whenever either hours or rate given to shift_pay is NULL, empty text, or text that is not wholly a number, it returns NULL; numeric text such as '45' and '1000' is read as a number.
- Whenever ship_cost is given a parcel weight in grams and a zone, a parcel weighing more than 0 grams has its first started kilogram charged a base charge of 300 cents for zone A, 500 for zone B and 800 for zone C. Then add 100 cents for zone A, 150 for zone B or 200 for zone C per 500 g block of weight beyond the first kilogram, with the number of blocks rounded up. A parcel weighing 0 grams costs 0 cents (see rule 46).
- Whenever a parcel given to ship_cost weighs more than 1000 grams, it is charged what a 1000 g parcel in that zone costs (the zone's base charge plus one 500 g block charge, as in rule 72), plus one 500 g block charge for that zone (100 cents for zone A, 150 for zone B, 200 for zone C) for each started 500 g block of weight beyond 1000 g, where any part of a block rounds up to a full block, so a further started kilogram is no longer charged as a full 300 cents (1001 g in zone A is 600 cents, which is 6 rupees: 500 for the first 1000 g plus 100 for the one started block beyond it).
- Whenever a parcel given to ship_cost weighs 0 grams, it costs 0 cents (0 rupees) in every valid zone, with no base charge. Whenever it weighs more than 0 grams but less than a kilogram, it is charged the zone's base charge as one started kilogram (0.1 g in zone A gives 400).
- Whenever the weight given to ship_cost is negative, it returns NULL (no charge is quoted).
- Whenever the zone given to ship_cost is written in lower case or with spaces around it (' b ', 'c'), it is recognised as that zone.
- Whenever the zone given to ship_cost is anything other than A, B or C (such as 'D', 'AA', empty text or a number), the zone is treated as unknown and the parcel is charged at zone C rates (a base charge of 800 cents for the first started kilogram, and 200 cents per started 500 g block beyond the first kilogram), with weight handled exactly as in the other rules (0 grams costs 0 cents, and a negative weight still returns NULL). A NULL zone is not an unknown zone: it still returns NULL (see rule 50).
- Whenever the weight or zone given to ship_cost is NULL, it returns NULL.
- Whenever the weight given to ship_cost is text, a leading number is used ('2500' or '2500kg' is 2500 g), and text with no leading number (such as 'abc' or empty text) is treated as 0 grams and therefore costs 0 cents, the same as a 0 g parcel, provided the zone is not NULL (an unknown zone is treated as zone C, see rule 49).
- Whenever slugify is given a title, it returns it in lower case with every run of characters other than the English letters a-z and digits 0-9 (spaces, punctuation, underscores, slashes, tabs, dots) replaced by a single hyphen ('Hello, World!' becomes 'hello-world'; 'a_b-c/d.e' becomes 'a-b-c-d-e').
- Whenever slugify produces hyphens at the start or end, it removes them, so leading and trailing spaces or punctuation leave no hyphen ('  Hello   World  ' becomes 'hello-world', '---x---' becomes 'x'), and repeated separators collapse to one hyphen.
- Whenever slugify is given accented letters (Café Crème Brûlée, Ñandú, Über), it drops the accent and keeps the base letter ('cafe-creme-brulee', 'nandu', 'uber').
- Whenever slugify is given letters that have a standard plain-letter spelling but are not just an accented base letter, it writes them out in plain letters: æ becomes 'ae', œ becomes 'oe', and ø becomes 'o', so 'Œuvre æ ø' becomes 'oeuvre-ae-o'. The letter ß (and capital ẞ) is not written out as 'ss'. It is treated like any other letter with no plain-letter equivalent, so it acts as a separator and is dropped, and 'Größe Straße' becomes 'gro-e-stra-e' (ö still loses its accent and becomes o under the accent rule). Whenever slugify is given letters with no plain-letter equivalent at all (such as Japanese characters), it treats them as separators and drops them.
- Whenever slugify is given full-width letters and digits, ligatures or circled digits, it converts them to their plain forms ('ＡＢＣ １２３' becomes 'abc-123', 'ﬁne' becomes 'fine', '①②' becomes '12'); symbols such as ™ and © are dropped ('x™ y©' becomes 'xtm-y').
- Whenever slugify is given NULL it returns NULL; whenever it is given empty text, or text with no letters or digits at all (such as '!!!'), it returns empty text.
- Whenever slugify is given a number, it uses the number's text, so 12345 becomes '12345' and 1.5 becomes '1-5'.
- Whenever robust_mean is given a column with 3 or more non-NULL values, it sets aside exactly one lowest and one highest value and returns the average of the rest (1, 2, 3, 4, 100 gives 3; 1, 2, 100 gives 2).
- Whenever the lowest or highest value in robust_mean is repeated, only one copy of each is set aside (1, 1, 1, 10 gives 1).
- Whenever robust_mean is given only 1 or 2 non-NULL values, nothing is set aside and it returns NULL (blank), not an average (5 gives NULL; 1 and 3 give NULL; 10 and 1000 give NULL).
- Whenever robust_mean meets NULL values, it ignores them completely and does not count them toward the 3 values needed for trimming (1, 2, NULL, 3, NULL gives 2; 1, 2, NULL gives NULL because only 2 values count).
- Whenever robust_mean has no rows, only NULL values, or fewer than 3 non-NULL values, it returns NULL.
- Whenever robust_mean is given a text value in a numeric column, it counts text that starts with a number as that leading number ('5x' as 5, '10' as 10) and text with no leading number (such as 'abc' or empty text) as 0, and that value still takes part in the trimming and the average.
- Whenever robust_mean is used with a filter or grouping, it is calculated separately on the rows of each group (1,3,20 gives 3 and 2,10,30 gives 10), a group with fewer than 3 non-NULL values gives NULL, and when the result is a number it is always a decimal number (such as 5.0).
- Leela works 41 hours at 20 rupees an hour: the 41st hour is paid at one and a half times, so her pay comes to 830 rupees. The owner says: Right now? 3: Enter
9: Enter
10: Enter
11: Enter
12: Enter
- Whenever an amount in hours is converted to rupees, it is charged at 35 rupees per hour, so 200 hours comes to 7,000 rupees.
- A title made only of spaces becomes an empty web address. The owner says: 19: Enter
20: Enter
- A shop whose sales amounts are all missing: the average is blank. The owner says: 22: Enter
23: Enter
24: Enter
- An order placed Monday 4 March 2024 is delivered Saturday 9 March: it comes to 5 working days. The owner says: 25: Enter
26: Enter
- Ravi's 100-rupee invoice is paid 7 days late: it is within the grace period, so the late fee is 0 rupees. The owner says: No, 7 days late is past the grace period, so the fee should be 5 rupees.
- Whenever a parcel given to ship_cost weighs exactly 1000 grams (1 kg), it is charged the zone's base charge plus one 500 g block charge for that zone (100 cents for zone A, 150 for zone B, 200 for zone C), so 1000 g in zone A costs 500 cents (5 rupees).

## QA
There is no product owner to ask on this project: `tools/ask.py` will tell you so.

### The owner's answers
The team recorded these questions overnight and the owner answered them this morning. Build to his answers.

- Q: Shift pay: overtime starts after how many hours in a week, and at what multiple of the hourly rate (we assumed after 40 hours at 1.5x)?
  A: Yes, 1.5x after 40 hours, but it's per shift, not per week. Over 60 hours it goes to 2x.
- Q: Shift pay: when the overtime or fractional-hour pay has a fraction of a cent, do we round to the nearest cent (half up) or round down?
  A: Round to the nearest cent, with exact halves going up. Don't round down.
- Q: Shift pay: if hours or rate is negative, should pay be 0 (our guess), blank, or an error?
  A: Neither, don't clamp it. Negative hours or a negative rate should give negative pay (negative hours at the normal rate), not 0, blank, or an error.
- Q: Shipping: what is the charge for each zone (A, B, C and any others) and each weight band? We assumed first 500 g costs A 400 / B 600 / C 800 cents, plus 100 / 200 / 250 cents per further started 500 g.
  A: No, your assumption is off. There's no separate first-500g price, just a base plus a per-block charge, where each started 500 g is a block, including the first.

- **A:** 300 base + 100 per block
- **B:** 500 base + 150 per block
- **C:** 800 base + 200 per block

Zone matching ignores case and spaces. Any other zone is charged at C rates.

Over 20000 g, add 1500 for oversize. Exactly 20000 g gets no surcharge. Weight of 0 or less costs 0.
- Q: Shipping: what should happen for an unknown or blank zone (we return blank), and for zero or negative weight (we charge 0)?
  A: Unknown or blank zone should charge zone C rates, not return blank. Only a NULL zone returns blank. Zero or negative weight returning 0 is correct.
- Q: Shipping: is there a maximum weight we ship, or a cap on the charge?
  A: No max weight, we ship anything. Only extra is a flat 1500 cents surcharge once it's over 20,000 g, and there's no cap on the charge.
- Q: Card masking: how many trailing digits should stay visible (we assumed last 4)?
  A: Last 4 by default. Exception: a 15-digit card starting with 3 (Amex) shows the last 5. Anything with fewer than 5 digits gets fully starred.
- Q: Card masking: if the text has 4 or fewer digits, should we mask all of them (our guess) or show it unchanged?
  A: Mask them all: with fewer than 5 digits, every digit becomes '*'.
- Q: Card masking: should spaces and dashes be kept in place (we keep them), and what about letters or other characters in the text?
  A: Yes, keep spaces and dashes in place. Letters and any other non-digit characters get kept unchanged too. Only the digits 0-9 get masked.
- Q: For the outlier-resistant average (robust_mean), do we always drop exactly the single highest and single lowest value, or drop a percentage (e.g. 20%) from each end? My guess: drop one from each end.
  A: Yes, drop exactly one lowest and one highest, not a percentage. If the min or max repeats, only remove one copy of each.
- Q: For robust_mean, what should it return when there are fewer than 3 values (1 or 2)? My guess: the plain average of what is there; NULL only if there are no values.
  A: No, return NULL whenever there are fewer than 3 numeric values, so 1 or 2 values gives NULL, not a plain average.
- Q: For robust_mean, should blank or non-numeric text values be ignored like empty values, or counted as zero? My guess: NULLs ignored, numeric-looking text treated as numbers.
  A: Text values get ignored, same as NULLs, and only actual numbers count. Don't convert text to numbers, even numeric-looking text, and never treat anything as zero.
- Q: For slugify, should accented letters be converted to plain letters (café -> cafe) or dropped/kept? My guess: converted to plain letters.
  A: Yes, convert them to plain letters (café -> cafe) by removing the accent marks. Your guess is right.
- Q: For slugify, should there be a maximum slug length? My guess: no limit.
  A: Yes, cap it at 30 characters. If the cut leaves a hyphen at the end, remove it.
- Q: For slugify, what should a title with no letters or digits (e.g. '!!!' or blank) return: empty text or NULL? My guess: empty text; a missing (NULL) title gives NULL.
  A: Yes, your guess is right. No letters or digits gives empty text, and a NULL title gives NULL.
- Q: For slugify, should an ampersand be spelled out as 'and' (Tom & Jerry -> tom-and-jerry) or just treated as a separator? My guess: separator.
  A: Separator. Every non-a-z/0-9 character is just a separator, so "Tom & Jerry" becomes tom-jerry.
- Q: Age in years: if someone was born on 29 February, do they turn a year older on 28 February or 1 March in non-leap years? We assumed 1 March.
  A: 1 March is right. In non-leap years they turn a year older on 1 March, and in leap years on 29 February.
- Q: Age in years: if the birth date is after the as-of date, or either date is blank or not a valid date, do we return blank (our guess), 0, or a negative age?
  A: Blank for a missing or invalid date. If the birth date is after the as-of date, return a negative age (no clamping to 0).
- Q: Working days: is the end date counted? We assumed the start date counts and the end date does not (Mon 4 Mar to Mon 11 Mar = 5), and that Saturday/Sunday are the only days off.
  A: Right on the counting: start day counts if it's a working day, end day never does. But Saturday and Sunday aren't the only days off. Dec 25 and Jan 1 are also non-working every year.
- Q: Working days: should public holidays be excluded, and if so which calendar? We assumed none.
  A: Only Dec 25 and Jan 1, every year, are non-working days. No other holidays and no regional calendar. Weekends are off too.
- Q: Working days: if the end date is before the start date, return a negative count (our guess), 0, or blank?
  A: Return 0.
- Q: Course grades: are the cut-offs A 90, B 80, C 70, D 60 and F below 60? We assumed so, with no rounding (89.9 is a B).
  A: Cut-offs are right, but round the score to the nearest whole number first (halves up), so 89.5 becomes 90 and is an A. 89.9 is an A, not a B. Anything under 0 or over 100 after rounding is INVALID.
- Q: Course grades: what letter for a score above 100 (we give A), a negative score (F), and a blank or non-numeric score (blank)?
  A: Above 100 and below 0 should both be INVALID, not A or F. Blank or non-numeric should return NULL, as you said.

One exception: scores from -0.5 up to 0 round to 0 and get an F, and 100.01 to 100.49 round to 100 and get an A+.
- Q: Late fee: what are the fee percentages by days late? We assumed no fee up to 7 days, 2% from 8 days, 5% from 30 days, 9% from 60 days.
  A: Not quite. No fee up to 5 days late. After that it's 1% of the amount per late week (part-week counts as a full week), minimum 500 cents, capped at 25% of the amount.
- Q: Late fee: is there a minimum or maximum fee, and do we round fractions of a cent to nearest (our guess) or down? What about zero/negative amounts or days (we charge 0)?
  A: Round down, not to nearest. Minimum is 500 cents and the max is 25% of the amount, and the cap wins, so small invoices pay at most a quarter. 5 days late or fewer is 0, and zero amount past the grace period is 0, but a negative amount past the grace period gives the negative cap (amount/4, rounded down).
- Q: Loyalty points: what is the earning rate for each tier? We assumed 1 point per dollar basic, 1.5 silver, 2 gold, 3 platinum, rounded down.
  A: Close, but there's no platinum tier. Basic is 1.0, silver is 1.5 and gold is 2.0, so points are the amount in cents times the multiplier, divided by 100 and rounded down. Anything unknown or missing counts as basic, and points are capped at 5000 per purchase.
- Q: Loyalty points: what should an unknown or blank tier earn (we assume basic rate), and a zero or negative purchase (we give 0)?
  A: Unknown or blank tier: yes, basic rate. Zero purchase gives 0, but a negative purchase shouldn't be 0. Return the negative points (amount × multiplier ÷ 100, rounded down), with no floor at zero.
