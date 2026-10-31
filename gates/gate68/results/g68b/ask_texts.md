# Gate 55 ask texts (gates/gate55/referee/review55.py)

## N0
There is no product owner to ask on this project: `tools/ask.py` will tell you so. Work from the spec and the examples.

## CQ
The product owner is available on his phone, though busy: ask him with `python3 /home/claude/hive/gates/gate68/referee/ask_owner.py 7691 "<your question>"`. Ask in plain business words, one decision per question; he answers in a sentence or two. (`tools/ask.py` is not used on this project.) **Before you build each function, ask him about every business decision its one-line spec leaves open**: cut-offs and boundaries, rounding, minimums and caps, what happens with blank, missing, negative or oddly formatted input. Build to his answers.

## SQ
The product owner is available on his phone, though busy: ask him with `python3 /home/claude/hive/gates/gate68/referee/ask_owner.py 7692 "<your question>"`. Ask in plain business words, one decision per question; he answers in a sentence or two. (`tools/ask.py` is not used on this project.) **Before you build each function, ask him about every business decision its one-line spec leaves open**: cut-offs and boundaries, rounding, minimums and caps, what happens with blank, missing, negative or oddly formatted input. Build to his answers. Your teammates ask him too: first read every answer he has given so far with `python3 /home/claude/hive/gates/gate68/referee/ask_owner.py 7692 --answers`, and do not ask again what he has already answered.

## SQH
There is no product owner to ask on this project: `tools/ask.py` will tell you so.

### The owner's rules for this feature (from his interview)
The owner decided each of these himself. Encode every one that touches your area as a test before you land, follow it exactly, and do not stretch it beyond the situation it describes.

- biz_days: Whenever both dates are valid 'YYYY-MM-DD' dates, the result is the number of Monday-to-Friday days after the start date up to and including the end date; the start date itself is never counted (e.g. Mon 2024-01-01 to Mon 2024-01-08 gives 5).
- biz_days: Whenever the end date is the same as or earlier than the start date, the result is 0.
- biz_days: Whenever a day in the range falls on a Saturday or Sunday, it is not counted (Saturday 2024-01-06 to Sunday 2024-01-07 gives 0).
- biz_days: Whenever a day in the range is December 25 or January 1, it is not counted, even if it is a weekday, in every year (2024-12-24 to 2024-12-26 gives 1). No other holidays are recognised.
- biz_days: Whenever the start date is a holiday or weekend, it makes no difference, because the start date is never counted; whenever the end date is a weekday that is not a holiday, it is counted.
- biz_days: Whenever either date is NULL, the result is NULL, even if the other date is not a valid date.
- biz_days: Whenever either date is not valid text in exactly the form YYYY-MM-DD with a real calendar date (empty text, a number, a missing leading zero like '2024-1-1', a date with a time, an impossible date like 2024-02-30, or year 0000), the result is -1.
- biz_days: Whenever a valid date has spaces before or after it, the spaces are ignored and the date is used normally.
- biz_days: Whenever the range includes February 29 of a leap year, that day is counted like any other weekday (2024-02-28 to 2024-03-01 gives 2; 2023-02-28 to 2023-03-01 gives 1).
- late_fee: Whenever the invoice is 3 days late or fewer (including 0 or negative days), the fee is 0.00; the fee starts only at more than 3 days (3.01 days already counts as late).
- late_fee: Whenever the invoice is more than 3 days late, the base fee is 1.5% of the balance for each week late, and any part of a week counts as a full week (4 to 7 days is one week, 8 to 14 days is two weeks; a 1000.00 balance gives 15.00 at 7 days and 30.00 at 8 days).
- late_fee: Whenever the base fee is under 5.00 and the invoice is more than 3 days late, the fee is raised to a minimum of 5.00 (a 100.00 balance 4 days late is charged 5.00).
- late_fee: Whenever the fee would be more than 25% of the balance, it is capped at 25% of the balance, and this cap overrides the 5.00 minimum (a 10.00 balance more than 3 days late is charged 2.50; a 4.00 balance 10 days late is charged 1.00).
- late_fee: Whenever the fee has fractions of a cent, it is rounded down to the whole cent, never up (a 1234.57 balance 10 days late gives 37.03, not 37.04; a 0.01 balance gives 0.00).
- late_fee: Whenever the balance is zero or negative, the fee is 0.00, however late the invoice is.
- late_fee: Whenever either the balance or the days late is NULL, the result is NULL.
- late_fee: Whenever the balance or days late is given as text, numeric text such as '200' or ' 500 ' is accepted and its number is used. Text that is not entirely a number, such as '10abc', 'abc' or empty text, gives NULL instead of 0 (the fee is NULL, not 0.00); the number at the start of the text is not used.
- late_fee: Whenever the days late is a fraction, any amount over 3 days is charged and rounded up to a whole week (3.5 days on a 500.00 balance gives 7.50).
- loyalty_tier: Whenever the points balance is from 0 up to just under 1000, the tier is 'Bronze'.
- loyalty_tier: Whenever the points balance is 1000 or more but under 5000, the tier is 'Silver'; exactly 1000 is Silver and 4999 is still Silver.
- loyalty_tier: Whenever the points balance is 5000 or more but under 20000, the tier is 'Gold'; exactly 5000 is Gold and 19999.9 is still Gold.
- loyalty_tier: Whenever the points balance is 20000 or more, the tier is 'Platinum'; exactly 20000 is Platinum.
- loyalty_tier: Whenever the points balance is below zero (even -0.5), the tier is 'Closed'.
- loyalty_tier: Whenever the points balance has a fraction, it is not rounded; 999.99 is Bronze.
- loyalty_tier: Whenever the points balance is NULL, the result is NULL.
- loyalty_tier: Whenever the points are given as text, the whole text must be a number ('5000' is Gold, '1500' is Silver). Text that isn't a number gives NULL and is never treated as zero points or given a tier. This includes words such as 'abc', text with a leading number followed by other characters such as '1500abc', and empty text.
- make_slug: Whenever a title is given, the slug is the title in lower case with every run of characters other than letters a-z and digits 0-9 (spaces, punctuation, underscores, slashes, apostrophes, dots, commas) replaced by a single hyphen ('A_B/C.D!' gives 'a-b-c-d'; 'Tom''s' gives 'tom-s'; '1,000 items' gives '1-000-items').
- make_slug: Whenever the title has leading or trailing spaces or symbols, or repeated spaces, no leading, trailing or doubled hyphens appear ('  Hello   World  ' gives 'hello-world').
- make_slug: Whenever the title contains an ampersand, it is read as the word 'and' ('Rock & Roll' and 'Rock&Roll' both give 'rock-and-roll').
- make_slug: Whenever the title has accented letters that can be split into a plain letter and an accent, the accent is dropped and the plain letter kept ('Café Crème' gives 'cafe-creme'); full-width letters such as 'ＡＢＣ' become plain 'abc'.
- make_slug: Whenever the title has letters with no plain-letter equivalent (Japanese, Æ, Ø, ß), those characters are treated as symbols and dropped, becoming a hyphen between other words.
- make_slug: Whenever the slug would be longer than 40 characters, it is cut at 40 characters, and a hyphen left at the end by the cut is removed, so the slug may be 39 characters.
- make_slug: Whenever the title is empty, only spaces, only symbols, or only characters with no Latin equivalent, the slug is 'untitled'.
- make_slug: Whenever the title is NULL, the result is NULL.
- make_slug: Whenever the title is a number, it is treated as its text ('12345' gives '12345', 1.5 gives '1-5', and 1.0 gives '1').
- mask_card: Whenever the card number has 5 or more digits, every digit except the last 4 is replaced by '*' and the last 4 are shown, giving one '*' per hidden digit ('4111111111111111' gives '************1111').
- mask_card: Whenever the card number contains spaces, hyphens, letters or other non-digit characters, those are removed first and are not shown in the result ('4111-1111-1111-1111' gives '************1111').
- mask_card: Whenever the card number has 1 to 4 digits, all of them are hidden: the result is one '*' per digit ('1234' gives '****', '12' gives '**').
- mask_card: Whenever the card number has no digits at all (empty text, only spaces, or only letters), the result is empty text.
- mask_card: Whenever the card number is given as a numeric value instead of text, it is treated as its digits; a minus sign and decimal point are dropped (-1234567 gives '***4567'; 123456.5 gives '***4565'; 0 gives '*').
- mask_card: Whenever the card number is NULL, the result is NULL.
- mask_card: Whenever the number is very long (more than 16 digits), the same rule applies with no limit: all but the last 4 digits are starred.
- norm_phone: Whenever the text holds exactly 10 digits after removing all non-digit characters (spaces, brackets, hyphens, dots, plus signs), the result is '+1' followed by those 10 digits ('(555) 123-4567' gives '+15551234567').
- norm_phone: Whenever the text holds exactly 11 digits that begin with 1, the result is '+' followed by the 11 digits ('1-555-123-4567' and '+1 555 123 4567' give '+15551234567').
- norm_phone: Whenever the text contains the letter x or the letters ext (in any letter case), everything from the first such marker onwards is ignored as an extension, and the rest is judged as above ('555-123-4567 ext. 89' gives '+15551234567'; a bare trailing 'x' is also ignored).
- norm_phone: Whenever an x or 'ext' appears before the digits, such as 'x555-123-4567', everything is cut off and the result is 'INVALID'.
- norm_phone: Whenever any other letters sit in the text, they are ignored when counting digits; but a word containing an x or 'ext' (such as 'extra') cuts the text off there ('555-123-4567 extra' still works; 'Text 555 123 4567' becomes INVALID because the cut leaves no digits).
- norm_phone: Whenever the digit count is anything other than 10, or 11 starting with 1 (international numbers like '+44 20 7946 0958', 11 digits starting with another digit, 12 digits, short numbers, empty text, or text with no digits), the result is 'INVALID'.
- norm_phone: Whenever a 10-digit number starts with 0 or 1 (for example '0555123456'), it is accepted without checking the area code, and '+1' is put in front.
- norm_phone: Whenever the phone is a numeric value (5551234567 or 15551234567), it is treated as its digits and normalised the same way.
- norm_phone: Whenever the text is NULL, the result is NULL (not 'INVALID').
- overtime_pay: Whenever hours are 40 or fewer, pay is hours times rate (37.5 hours at 18.50 gives 693.75).
- overtime_pay: Whenever hours are above 40 up to 60, the first 40 hours are paid at the normal rate and each hour from 40 to 60 at 1.5 times the rate (41 hours at 10.00 gives 415.00; 60 hours gives 700.00).
- overtime_pay: Whenever hours are above 60, each hour above 60 is paid at double the rate, on top of the earlier bands (61 hours at 10.00 gives 720.00; 80 hours gives 1100.00).
- overtime_pay: Whenever hours are negative, the pay is 0.00, even if the rate is also negative.
- overtime_pay: Whenever the rate is negative and hours are not negative, the pay is negative by the same calculation (10 hours at -10 gives -100.00); a zero rate or zero hours gives 0.00.
- overtime_pay: Whenever the pay has fractions of a cent, it is rounded to the nearest cent with exactly half a cent rounding up (rate 0.005 for 1 hour gives 0.01; 41 hours at 10.005 gives 415.21).
- overtime_pay: Whenever hours or rate is NULL, the result is NULL, even if the other value is negative or text.
- overtime_pay: Whenever hours or rate is given as text that is wholly a number (spaces around it allowed, such as ' 45 ' or '4e1'), it is used as that number.
- overtime_pay: Whenever hours or rate is text that is not wholly a number ('abc', empty text, '45abc', '1,5'), the pay is NULL, so '45abc' hours gives NULL pay. Numeric text such as ' 45 ' or '4e1' is still accepted as a number.
- overtime_pay: Whenever hours or rate is infinite or not-a-number (including the text 'inf' or 'nan', or a value too large to store), the result is NULL.
- review_stars: Whenever there are 5 or more votes, the stars shown are the average rounded to the nearest half star, with an exact quarter point rounding up (4.24 gives 4.0, 4.25 gives 4.5, 4.74 gives 4.5, 4.75 gives 5.0, 2.25 gives 2.5).
- review_stars: Whenever there are fewer than 5 votes (including 0, negative, or 4.9), the result is the text 'n/a' no matter the average; exactly 5 votes is enough. (Votes that are not a number at all are not covered here; see rule 65.)
- review_stars: Whenever the average is above 5, the stars shown are 5.0; whenever it is below 0, they are 0.0.
- review_stars: Whenever the average is text that is wholly a number ('4.5'), it is used as that number; whenever it is any other text or empty, it is NULL (not 0, and not 0.0 stars) (when there are enough votes). Likewise, whenever the votes is text that is not a number (such as 'abc') or is empty, the result is NULL, not 'n/a', no matter what the average is.
- review_stars: Whenever the average or votes is NULL, the result is NULL, even if the other value would give 'n/a'.
- review_stars: Whenever the average or votes is infinite or too large to store, the result is NULL, and this check happens before the votes check.
- split_bill: Whenever the bill is shared, each person pays (total plus tip percent of the total) divided by the number of people (100 with 20% tip among 4 gives 30.00).
- split_bill: Whenever the share has fractions of a cent, it is rounded up to the next whole cent, never down (100 split 3 ways with no tip gives 33.34).
- split_bill: Whenever the tip percentage is above 30, it is treated as 30 (100 among 4 with 50% tip gives 32.50).
- split_bill: Whenever the tip percentage is negative, it is applied as a discount with no lower limit (-10% on 100 among 4 gives 22.50; -200% gives -25.00).
- split_bill: Whenever the number of people is 0 or negative, or NULL, the result is NULL.
- split_bill: Whenever the number of people is a fraction above 0, it is used as is, with no rounding (2.5 people gives 44.00 for 100 with 10% tip).
- split_bill: Whenever the total is negative, the result is negative by the same calculation (-100 among 4 with 10% tip gives -27.50); a zero total gives 0.00.
- split_bill: Whenever the total, people or tip is NULL, the result is NULL, even if the people number is 0.
- split_bill: Whenever the total or tip is text that is not wholly a number ('abc', empty text), it counts as NULL, so a bad total gives NULL and a bad tip gives NULL; numeric text like '100' is still accepted and used as a number.
- split_bill: Whenever the people value is text that is not wholly a number ('abc'), the result is NULL because it counts as 0 people.
- split_bill: Whenever the total, people or tip is infinite or too large to store, the result is NULL.
- mid_value: Whenever a column has an odd number of numeric values, the result is the middle one when sorted from smallest to largest (3, 1, 2 gives 2).
- mid_value: Whenever a column has an even number of numeric values, the result is the lower of the two middle values, not their average (1, 2, 3, 4 gives 2; 4, 1 gives 1).
- mid_value: Whenever values are NULL or text (including numeric-looking text such as '5'), they are ignored and not counted.
- mid_value: Whenever there are no numeric values at all (no rows, all NULL, only text, or no rows matching a filter), the result is NULL.
- mid_value: Whenever the aggregate is used with GROUP BY, each group gets its own middle value, calculated only from that group's numeric values.
- mid_value: Whenever the middle value is a whole number or a decimal, it is returned exactly as stored, with no rounding.
- Hours entered as the word abc at 20 dollars an hour pay 0 dollars, with no warning. The owner says: Case 39 is wrong: "abc" isn't a number, so it should give a blank (NULL), not 0 dollars.
