# Gate 55 ask texts (gates/gate55/referee/review55.py)

## N0
There is no product owner to ask on this project: `tools/ask.py` will tell you so. Work from the spec and the examples.

## SF
There is no product owner to ask on this project: `tools/ask.py` will tell you so.

### The owner's rules for this feature (from his interview)
The owner decided each of these himself. Encode every one that touches your area as a test before you land, follow it exactly, and do not stretch it beyond the situation it describes.

- bulk_price: Whenever an order is priced, the total is the unit price times the quantity, with one discount rate applied to the whole order (not just the extra units), and the result is a whole number of cents.
- bulk_price: Whenever the quantity is 1 to 9 there is no discount; at 10 to 49 units the whole order gets 5% off; at 50 to 99 units 10% off; at 100 or more units 15% off.
- bulk_price: Whenever the discounted total has a fraction of a cent, it is rounded to the nearest cent with exactly half a cent rounded up (for example 15 cents x 10 units gives 143, and 105 cents x 10 units gives 998).
- bulk_price: Whenever the unit price or the quantity is NULL, the total is NULL.
- Whenever the unit price is negative or the quantity is negative, the total is 0 (not NULL, and not an error).
- bulk_price: Whenever the unit price is 0 or the quantity is 0, the total is 0.
- bulk_price: Whenever the unit price or quantity is empty text or text that is not a number (such as 'abc'), the total is NULL.
- bulk_price: Whenever the unit price or quantity is given as numeric text such as '100' or ' 100 ', it is treated as that number and priced normally.
- bulk_price: Whenever the quantity has a fraction (for example 10.5), only the whole units are charged (10.5 is charged as 10), but the discount tier is chosen from the unchanged quantity, so 9.9 gets no discount and 49.9 gets the 5% tier.
- bulk_price: Whenever the unit price has a fraction of a cent (for example 99.5), the fraction of the undiscounted total (unit price x whole units) is dropped before the discount is applied, so 99.5 x 1 gives 99 and 10.5 x 10 gives 100.
- fiscal_label: Whenever a valid date is given, the label has the form FY<year>-Q<n>, where the fiscal year begins on 1 April and is named after the calendar year in which it ends (1 April 2024 to 31 March 2025 is FY2025).
- fiscal_label: Whenever the month is April to June the quarter is Q1, July to September is Q2, October to December is Q3, and January to March is Q4; for example 2024-04-01 is FY2025-Q1, 2024-12-31 is FY2025-Q3, 2025-01-01 is FY2025-Q4 and 2024-03-31 is FY2024-Q4.
- fiscal_label: Whenever the year is shorter than four digits of significance, the fiscal year is shown with at least four digits (0099-05-10 gives FY0100-Q1), and a fiscal year that reaches 10000 is shown in full (9999-12-31 gives FY10000-Q3).
- fiscal_label: Whenever the month is not 01 to 12 or the day is not 01 to 31, the label is NULL (for example month 13, month 00, day 00 or day 32).
- fiscal_label: Whenever the day is within 1 to 31, the date is accepted even if it does not exist on the calendar (2024-02-31, 2023-02-29 and 2024-04-31 all get a label based on their month).
- fiscal_label: Whenever the date has spaces before or after it, the spaces are ignored and the label is produced normally.
- fiscal_label: Whenever the text is not exactly four digits, a dash, two digits, a dash, two digits (for example 2024/05/10, 2024-5-10, a date with a time after it, or 'abc'), the label is NULL.
- fiscal_label: Whenever the date is NULL, empty text, or a number rather than text (such as 20240510), the label is NULL.
- isbn_check: Whenever a code of exactly nine digits is given, the result is the ISBN-10 check digit: the digits are multiplied by 10, 9, 8 ... 2 in order, summed, and the check digit is whatever brings the sum up to a multiple of 11 (for example 030640615 gives 2, and 000000000 gives 0).
- isbn_check: Whenever the check digit works out to 10, the result is the capital letter X (for example 123456789 and 080442957 give X).
- isbn_check: Whenever the code contains hyphens or spaces, they are removed before counting, so '0-306-40615', '030 640 615' and ' 030640615 ' all give 2; other separators such as underscores or a plus sign make the result NULL.
- isbn_check: Whenever the code does not have exactly nine digits after removing hyphens and spaces (8 digits, 10 digits, or empty text), the result is NULL.
- isbn_check: Ignore letters (including 'x' or 'X') and any other non-digit characters in the code and use only the digits; the result is never NULL.
- isbn_check: Whenever the code is a whole number rather than text, it is padded with leading zeros to nine digits (30640615 is treated as 030640615 and gives 2; 0 gives 0), but a number with more than nine digits gives NULL.
- isbn_check: Whenever the code is a negative whole number, a decimal number (even 30640615.0), a binary value or NULL, the result is NULL.
- late_fee: No fee for the first 5 days late (an invoice 1 to 5 days late has no fee). After that, the fee is 2% of the amount per 30 days late, with a minimum fee of $5 and a cap of 20% of the amount. The rate applies to the whole amount.
- late_fee: Whenever the fee has a fraction of a cent, it is rounded to the nearest cent with exactly half a cent rounded up (25 cents at 2% gives 1, 24 cents gives 0).
- late_fee: Whenever days late is 0 or negative, or the amount is 0 or negative, the fee is 0.
- late_fee: Whenever the amount or days late is NULL, the fee is NULL, even if the other value is 0 or negative.
- late_fee: Whenever the amount or days late is empty text or text that is not a number, the fee is NULL; numeric text such as '10000' and '10' is used as that number.
- late_fee: Whenever days late has a fraction, it is not rounded before choosing the rate: 0.5 days counts as late at 2%, and 30.5 days falls into the 4% band.
- late_fee: Whenever the amount has a fraction of a cent, the fraction is dropped before the percentage is taken (10050.7 is treated as 10050).
- loyalty_tier: Whenever the points balance is below 1000, the tier is 'bronze'; from 1000 up to 4999 it is 'silver'; from 5000 up to 19999 it is 'gold'; 20000 or more it is 'platinum' (tier names are lower case).
- loyalty_tier: Whenever the points balance is 0, negative, or a fraction just below a boundary (such as 999.9), the tier is 'bronze'.
- loyalty_tier: Whenever the points balance is numeric text such as '5000' or ' 1500 ', it is used as that number.
- loyalty_tier: Whenever the points balance is NULL, empty text or text that is not a number, the tier is NULL.
- make_slug: Whenever a title is given, the slug is the title in lower case, with every run of characters that are not English letters or digits (spaces, punctuation, underscores, slashes, ampersands) replaced by a single dash, and no dash at the start or end (for example '  Hello,   World!! ' gives 'hello-world').
- make_slug: Whenever the title has accented letters, the accents are removed and the plain letter is kept (Café Crème Brûlée gives cafe-creme-brulee).
- make_slug: Whenever the title has letters with no plain English equivalent (such as ß, Æ or Japanese characters), those characters are dropped like punctuation, so 'Ünïcödé ß Æ ñ 日本語' gives 'unicode-n'.
- make_slug: Whenever the slug is longer than maxlen, it is cut to maxlen characters and any dash left at the end by the cut is removed, so the result can be shorter than maxlen ('Hello World' with maxlen 6 gives 'hello').
- make_slug: Whenever maxlen is 0 or negative, the slug is empty text (not NULL).
- make_slug: Whenever maxlen has a fraction it is cut down to the whole number (7.9 acts as 7), and numeric text such as '5' is used as that number; maxlen that is empty text or not a number gives NULL.
- make_slug: Whenever the title or maxlen is NULL, the slug is NULL.
- make_slug: Whenever the title is empty, contains only punctuation, or only dashes and spaces, the slug is empty text; a title given as a number is used as its digits ('12345' stays '12345').
- meeting_end: Whenever a valid start time and a number of minutes are given, the result is the start plus those minutes as HH:MM on a 24-hour clock with two-digit hours and minutes (09:00 plus 60 gives 10:00).
- meeting_end: Whenever the end falls past midnight, the time is capped at 23:59 and never wraps to the next day (23:30 plus 45 gives 23:59, 00:00 plus 1440 gives 23:59); this also holds for very long durations (10:00 plus 100000 gives 23:59).
- meeting_end: Whenever minutes is 0, the end equals the start; whenever minutes is negative, the result is NULL.
- meeting_end: Whenever the minutes have a fraction, the fraction is dropped (90.7 counts as 90, 0.5 as 0), and numeric text such as '30' is used as that number; empty or non-numeric text for minutes gives NULL.
- meeting_end: Whenever the start has a one-digit hour (9:05) or surrounding spaces, it is accepted and the result is still two-digit (09:35).
- meeting_end: Whenever the start includes seconds (09:00:45), the seconds are ignored and not counted, and are not validated beyond being two digits (09:00:99 is accepted).
- meeting_end: Whenever the start hour is above 23 or the minutes above 59 (24:00, 12:60), the result is NULL.
- meeting_end: Whenever the start is not in hours:minutes form (one-digit minutes such as 9:5, 0900, 09.00, a 12-hour time with PM, empty text, a number, or any other text), the result is NULL.
- meeting_end: Whenever the start or minutes is NULL, the result is NULL.
- pct_change: Whenever old and new are numbers and old is not 0, the result is (new minus old) divided by the size of old, times 100, rounded to 1 decimal place (100 to 110 gives 10.0, 3 to 4 gives 33.3, 100 to 0 gives -100.0).
- pct_change: Whenever old is negative, the change is measured against the positive size of old, so a rise in the value is always a positive percentage (-100 to -50 gives 50.0, -100 to -150 gives -50.0, -50 to 50 gives 200.0).
- pct_change: Whenever old is 0 (including 0.0 and '0'), the result is NULL, even if new is also 0.
- pct_change: Whenever old or new is NULL, the result is NULL.
- pct_change: Whenever old or new is empty text or text that is not a number, the result is NULL; numeric text such as '100' or ' 100 ' is used as that number.
- pct_change: Whenever the rounding falls exactly halfway between two 1-decimal values, it rounds away from zero (400 to 401 gives 0.3, 400 to 399 gives -0.3).
- pct_change: Whenever a very small decrease rounds to zero, the answer may display as -0.0 (100 to 99.95), and a very small increase gives 0.0.
- phone_fmt: Whenever a phone number has exactly 10 digits after all non-digit characters (spaces, dashes, dots, brackets, plus signs) are removed, it is shown as (AAA) EEE-NNNN, for example '212.555.1234' gives '(212) 555-1234'.
- phone_fmt: Whenever a phone number has 11 digits and the first is 1, that leading 1 (country code) is dropped and the remaining 10 digits are formatted ('+1 212 555 1234' and '1-212-555-1234' give '(212) 555-1234').
- phone_fmt: Whenever a phone number has 11 digits and the first is not 1 (22125551234), or has fewer than 10 or more than 11 digits, the result is NULL.
- phone_fmt: Whenever the area code or exchange begins with 0 or 1 (0125551234, 1125551234), it is still formatted; only the length is checked, not whether the number is a real North American number (1111111111 gives (111) 111-1111).
- phone_fmt: Whenever the number contains letters or an extension (212-555-CALL, '212 555 1234 ext 5'), the letters are ignored and only the digits count, so the result is NULL unless the digits themselves total 10 (or 11 with a leading 1); non-North-American numbers such as '+44 20 7946 0958' give NULL.
- phone_fmt: Whenever the number is a whole number such as 2125551234 or 12125551234, it is treated as its digits and formatted; a decimal such as 2125551234.0 gives NULL because of the extra digit from '.0'.
- phone_fmt: Whenever the phone number is NULL, empty, or only spaces, the result is NULL.
- phone_fmt: Whenever the number is written with digits from a non-Western script, those digits are counted and kept as written in the formatted result.
- avg_rating: Whenever a group of rows is averaged, the result is the plain average of the valid ratings, not rounded (ratings 1, 2, 2 give 1.6666666666666667), and each group is averaged separately when grouped.
- avg_rating: Whenever a rating is NULL, it is skipped and does not count in the average (4 and NULL give 4.0).
- avg_rating: Whenever a rating is outside the 1 to 5 scale (0, 0.5, 6, 5.5, -1), it is skipped as if absent, rather than treated as an error or clamped; 1 and 5 themselves and values like 4.5 are kept.
- avg_rating: Whenever a rating is empty text or text that is not a number, it is skipped; numeric text such as '4' or ' 4 ' counts as that number.
- avg_rating: Whenever there are no rows, or every rating in the group is NULL, invalid or out of range, the average is NULL.
- avg_rating: Whenever DISTINCT is written inside avg_rating, it has no effect: repeated ratings still each count (5, 5, 1 give 3.6666666666666665 either way).

## SS
There is no product owner to ask on this project: `tools/ask.py` will tell you so.

### The owner's rules for this feature (from his interview)
The owner decided each of these himself. Encode every one that touches your area as a test before you land, follow it exactly, and do not stretch it beyond the situation it describes.

- bulk_price: Whenever an order is for 10 to 49 units, the whole order (not just the units past 10) gets 5% off, while 1 to 9 units get no discount (1000 cents x 10 = 9500; x 9 = 9000).
- bulk_price: Whenever an order is for 50 to 99 units, the whole order gets 10% off (1000 cents x 50 = 45000).
- bulk_price: Whenever an order is for 100 or more units, the whole order gets 15% off, the largest discount (1000 cents x 100 = 85000).
- bulk_price: Whenever the discounted total is not a multiple of 5 cents, it is rounded to the nearest 5 cents with exact halves rounded up (995 cents x 10 = 9950, less 5% = 9452.5, charged as 9455).
- bulk_price: Whenever the quantity has a fraction, the fraction is charged too and also counts toward the discount tier (2.5 units at 1000 cents is charged 2500, i.e. 2.5 units).
- bulk_price: Whenever the unit price or the quantity is negative, no total is produced (blank) instead of an error or a credit (price -5, qty 3 gives blank).
- late_fee: Whenever an invoice is 1 to 30 days late, the fee is 2% of the invoice amount, except that nothing is charged for the first 5 days late (days 1 to 5 have a fee of 0). The 2% starts at day 6, and the minimum fee is 500 cents.
- late_fee: Whenever an invoice is 31 to 60 days late, the fee is 4% of the whole amount (10000 cents, 31 days late gives 400).
- Whenever an invoice is more than 60 days late, the fee is 6% of the whole amount, plus 2% of the whole amount for every extra 30 days late beyond 60 days (each full 30 days counts), with the total fee capped at 20% of the invoice (10000 cents, 61 days late gives 600; 10000 cents, 91 days late gives 800, which is 8%).
- late_fee: Whenever days late is 0 or negative (not yet overdue), or the invoice amount is zero or negative, the fee is 0 (10000 cents, 0 days gives 0).
- Whenever the fee is not a whole number of cents, it is rounded to the nearest cent with halves rounded up. The minimum fee is 500 cents, but the fee is never more than 20% of the invoice, so small invoices can be charged less than 500 cents.
- loyalty_tier: Whenever a customer has 1000 to 4999 points, the tier is 'silver' (1000 gives silver, 4999 gives silver); fewer than 1000 points, including negative balances, is 'bronze' (999 gives bronze).
- loyalty_tier: Whenever a customer has 5000 or more points, the tier is 'gold' (5000 gives gold), up to 19999 points. Whenever a customer has 20000 or more points, the tier is 'platinum' (20000 gives platinum).
- fiscal_label: Whenever a date falls on or after 1 April, the fiscal year is named for the following calendar year; 1 January to 31 March belongs to the year named for the same calendar year (2025-04-01 gives FY2026-Q1; 2025-03-31 gives FY2025-Q4).
- fiscal_label: Whenever the month is Apr-Jun it is Q1, Jul-Sep Q2, Oct-Dec Q3, Jan-Mar Q4 (2025-07-01 gives FY2026-Q2; 2025-12-15 gives FY2026-Q3).
- fiscal_label: Whenever the month is not 1 to 12, the day is not 1 to 31, or the date is not written YYYY-MM-DD with two-digit month and day, the result is blank (2025-13-01 and 2025-7-1 give blank).
- fiscal_label: Whenever a day is impossible for its month but within 1 to 31, it is NOT rejected and still gets a label (2025-02-30 gives FY2025-Q4; 2025-06-31 gives FY2026-Q1).
- isbn_check: Whenever a 9-digit code is given, the check digit is the standard ISBN-10 one, and a check value of 10 is shown as the letter X (030640615 gives 2; 123456789 gives X).
- isbn_check: Whenever the code is not exactly 9 digits (after ignoring hyphens and spaces), the result is blank rather than an error (12345 as text gives blank).
- make_slug: Whenever a title is turned into a slug, it is lower-case, accents are removed, and each run of spaces or punctuation becomes one hyphen with none at either end ('Hello, World!' gives hello-world; 'Café Crème' gives cafe-creme).
- make_slug: Whenever the slug is longer than maxlen, it is cut at maxlen characters, even mid-word, and a hyphen left at the cut is dropped ('Hello World' with 8 gives hello-wo; with 6 gives hello).
- make_slug: Whenever maxlen is 0 or negative, or the title has no letters or digits, the slug is empty text ('abc' with 0 gives an empty slug; '!!!' gives an empty slug).
- meeting_end: Whenever a booking runs past midnight, the end time is capped at 23:59 and does not wrap to the next day's clock time (23:30 plus 60 minutes gives 23:59; 09:30 plus 1500 minutes gives 23:59).
- meeting_end: Whenever the start is not a valid 24-hour time (hour above 23 or minutes above 59) or the duration is negative, the result is blank (start 25:00 gives blank; 09:30 minus 5 minutes gives blank).
- pct_change: Whenever the old value is 0, no percentage is produced (blank), not an infinite or 100% change (old 0, new 5 gives blank).
- pct_change: Whenever the change is computed, it is relative to the old value and rounded to 1 decimal place (old 3, new 4 gives 33.3; old 50, new 75 gives 50.0; old 100, new 80 gives -20.0).
- pct_change: Whenever the old value is negative, the change is measured against its size so that moving up is always positive (old -100, new -50 gives 50.0).
- phone_fmt: Whenever a phone number has 10 digits, or 11 digits starting with 1, it is shown as (AAA) EEE-NNNN with the leading 1 dropped (1 (415) 555-2671 gives (415) 555-2671).
- phone_fmt: Whenever a phone number has any other digit count (7 digits, 11 digits not starting with 1) or extra digits such as an extension, the result is blank (555-2671 gives blank; 415-555-2671 x12 gives blank).
- avg_rating: Whenever ratings are averaged, blank ratings and values outside 1 to 5 (such as 0 or 7) are ignored rather than counted, and no valid ratings gives blank (ratings 5, 4, blank, 0, 7, 3 average 4.0).
