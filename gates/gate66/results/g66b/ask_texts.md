# Gate 55 ask texts (gates/gate55/referee/review55.py)

## N0
There is no product owner to ask on this project: `tools/ask.py` will tell you so. Work from the spec and the examples.

## CC
The product owner is available on his phone, though busy: ask him with `python3 /home/claude/hive/gates/gate66/referee/ask_owner.py 7671 "<your question>"`. Ask in plain business words, one decision per question; he answers in a sentence or two. (`tools/ask.py` is not used on this project.)

## CQ
The product owner is available on his phone, though busy: ask him with `python3 /home/claude/hive/gates/gate66/referee/ask_owner.py 7672 "<your question>"`. Ask in plain business words, one decision per question; he answers in a sentence or two. (`tools/ask.py` is not used on this project.) **Before you build each function, ask him about every business decision its one-line spec leaves open**: cut-offs and boundaries, rounding, minimums and caps, what happens with blank, missing, negative or oddly formatted input. Build to his answers.

## HV
There is no product owner to ask on this project: `tools/ask.py` will tell you so.

### The owner's rules for this feature (from his interview)
The owner decided each of these himself. Encode every one that touches your area as a test before you land, follow it exactly, and do not stretch it beyond the situation it describes.

- bayes_rating: Whenever a product has an average and a vote count, the rating is (votes × average + 35) / (votes + 10), where the average is first clamped as rule 6 says if it is outside 0–5. This blends the (clamped) average with a prior of 10 imaginary votes at 3.5 stars, and the result is rounded to 2 decimals (halves round up). Example: average 4.5 with 100 votes gives 4.41. Example: average 9 with 10 votes is clamped to 5 first, giving 4.25, not 6.25.
- bayes_rating: Whenever the vote count is 0, the rating is 3.5 whatever the average is; with very many votes it approaches the average.
- bayes_rating: Whenever the vote count is negative (a whole number such as -3 or a fraction such as -0.5), it is treated as 0, and the rating is 3.5 whatever the average is (for example, a 4.8 average with -3 votes gives 3.5, not a blank rating or an error). This applies whenever the average and the vote count are both usable numbers; if either is NULL, empty text or text that is not a number, rule 4 still applies.
- bayes_rating: Whenever the average or the vote count is NULL, empty text, or text that is not a number, the rating is NULL.
- bayes_rating: Whenever the average or votes are numbers written as text (e.g. '4.5' and '20'), they are read as numbers and the rating is calculated normally.
- bayes_rating: Whenever the average is outside 0–5 (e.g. 9, 7 or -2), it is first clamped to the nearest limit, 5 if it is above 5 or 1 if it is below 1, and then the whole calculation (rule 1, and the vote-count rules 2, 3 and 7) proceeds with the clamped average, never the original one (average 9 is treated as 5, so with 10 votes the rating is 4.25; average 7 is treated as 5; average -2 is treated as 1). The rating can therefore never be above 5 because of a mistyped average.
- bayes_rating: Whenever the vote count is not a whole number (e.g. 2.5), it is used as is in the formula (4.5 average, 2.5 votes gives 3.7).
- initials: Whenever a full name is given, the result is the first character of each of the first 3 words only, in uppercase, joined together with no dots or spaces (e.g. 'ann marie lee' gives 'AML'). Any words after the third are ignored, even if they are small words like 'de', so 'Ana Maria de Souza' gives 'AMD' and 'ann marie lee jones' gives 'AML'. A name with fewer than 3 words uses all of its words.
- initials: Whenever words are separated by extra spaces, tabs or other whitespace, or the name has leading/trailing spaces, these are ignored and each word still counts once ('  john  smith ' gives 'JS').
- initials: Whenever a name contains a hyphen or apostrophe, it is not a word separator, so 'jean-paul sartre' gives 'JS' and "o'brien" gives 'O'.
- initials: Whenever a name starts with an accented letter, the accented letter is uppercased and used ('ánna élan' gives 'ÁÉ').
- initials: Whenever the name is NULL, the result is NULL; whenever it is empty or only spaces (so it has no words), the result is also NULL, not empty text.
- initials: Whenever the name is a number or a word starting with a digit, the first digit is used as its initial (123 gives '1', '1 2' gives '12'); there is no check that words are letters. Only the first 3 words count here too, so '1 2 3 4' gives '123'.
- Whenever an invoice is more than 3 days late, the fee is 0.5% of the amount for each day late, rounded to 2 decimals (halves round up). The first 3 days are a grace period (see rule 16). Example: 1000 that is 10 days late gives 50.00.
- For the first 3 days late there is no fee. This means any days late of 3 or less, including part days (for example 0.5, 2.5 or 3.0), gives a fee of 0.0. The fee starts only once days late is more than 3. The fee is never more than 25% of the amount. It grows by 0.5% of the amount per day until it reaches that 25% limit, which happens at 50 days late. From 50 days late onward it stays at 25% of the amount. Before that point the fee is not capped. Examples: 1000 gives 155.00 at 31 days, and 250.00 at 50 days and at any later day. 10000 at 31 days late gives 1550.00. 10000 at 2.5 days late gives 0.0.
- Whenever days late is 3 or less (this includes 0 and negative, and part-days such as 2.5), the fee is 0.0 (no penalty, because the first 3 days are a grace period), even if the amount is large. Exactly 3 days late is still within the grace period.
- late_fee: Whenever the amount is 0 or negative, the fee is 0.0 (no negative fees are produced).
- Whenever days late is a fraction, it is used as is, and the 3-day grace period applies to it like any other number (100 at 0.5 days gives 0.0, 10000 at 2.5 days gives 0.0, and 100 at 3.5 days gives 1.75); small fees round to 0.0 (0.5 amount, 1 day gives 0.0).
- late_fee: Whenever the amount or the days late is NULL, empty text, or text that is not a number, the fee is NULL; numbers written as text (e.g. '3') are read as numbers.
- late_fee: Whenever the amount or days late is NULL or non-numeric, the result is NULL even if the other value is zero or negative (the NULL check comes before the zero check).
- mask_email: Whenever an email has a name part of 3 or more characters, the first and last characters of the name are kept, everything between is replaced by asterisks (one per character), and the '@' and domain are left unchanged ('john.smith@example.com' gives 'j********h@example.com').
- mask_email: Whenever the name part has exactly 2 characters, both are fully masked with '*', so nothing of the name is shown, not even the first or last character, and the '@' and domain are left unchanged ('ab@x.com' gives '**@x.com'). Together with the 1-character rule, a name part of 1 or 2 characters is always fully hidden.
- mask_email: Whenever the name part has exactly 1 character, it is fully masked with * ('a@x.com' gives '*@x.com').
- mask_email: Whenever the name part is empty ('@x.com') or the whole text is empty, the result is NULL.
- mask_email: Whenever the text contains no '@', it is not an email address, so nothing is masked and the result is NULL (for example 'notanemail' gives NULL), whatever the text's length or characters.
- mask_email: Whenever the text contains more than one '@' sign, it is not a valid email address, so nothing is masked and the result is NULL, whatever the text's length or characters (for example 'a@b@c.com' gives NULL, and 'john@home@x.com' gives NULL).
- mask_email: Whenever the email has upper-case letters, they are kept as typed; the domain's case is also untouched.
- mask_email: Whenever the email has leading spaces or other characters, they count as part of the name (' bob@x.com' gives ' **b@x.com'); a number passed in is treated as text and masked the same way (12345 gives '1***5').
- mask_email: Whenever the email is NULL, the result is NULL.
- pro_rata: Whenever a service is used for some days of a period, the charge is amount × days used / days in period, rounded to 2 decimals (halves round up). Example: 300, 10 of 30 days gives 100.00; 100, 1 of 3 gives 33.33; 1, 1 of 8 gives 0.13.
- pro_rata: Whenever the days in the period is above 0 and days used exceeds the days in the period, days used is treated as the full period, so the whole amount is charged (300, 40 of 30 gives 300.00). This does not apply when the period is 0 or negative, where the result is 0.0.
- pro_rata: Whenever days used is negative, it is treated as 0 and the result is 0.0.
- pro_rata: Whenever the days in the period is 0 or negative, the result is 0.0, whatever the amount and the days used are (300, 10 of 0 days gives 0.0). This comes before the rule that treats days used above the period as the full period. The only exception is when any of the three values is NULL, empty or not a number, which still gives NULL.
- pro_rata: Whenever any of the three values is NULL, empty text, or text that is not a number, the result is NULL; numbers written as text ('300','10','30') are read as numbers.
- pro_rata: Whenever the amount is negative, the share is negative too (-300, 10 of 30 gives -100.0); amount 0 gives 0.0.
- pro_rata: Whenever days used is a fraction, it is used as is (300, 10.5 of 30 gives 105.0).
- ship_cost: Whenever a parcel has a weight above 0 and a zone, the cost is (4.90 + 1.20 × weight in kg) multiplied by 1.0 for zone A, 1.5 for zone B and 2.2 for zone C, then, if the weight is over 30 kg (exactly 30 kg or less gets none), a flat surcharge of 15 is added (the same 15 for every zone, not multiplied by the zone factor), and the total is rounded to 2 decimals (halves round up). Examples: 2 kg to A is 7.30, to B 10.95, to C 16.06 (no surcharge); 1000 kg to A is 1219.90.
- ship_cost: Whenever the weight is 0, the cost is NULL (no price), whatever the zone. A tiny weight above 0 such as 0.001 is still priced by the normal formula, so it comes to about the base charge: 4.9 for zone A, 7.35 for zone B, 10.78 for zone C.
- ship_cost: Whenever the weight is 0 or negative (less than or equal to 0), the cost is NULL; there is no maximum weight, so heavy parcels are still priced by the normal formula plus the flat 15 surcharge for weight over 30 kg (1000 kg to A costs 1219.90, 1000 kg to C costs 2665.78).
- ship_cost: Whenever the zone is lower case or has spaces around it ('b', ' c '), it is accepted as the same zone.
- ship_cost: Whenever the zone is anything other than A, B or C (e.g. 'D', empty text, 'AB', a number such as 1), the cost is billed as zone C.
- ship_cost: Whenever the weight or zone is NULL, or the weight is empty or non-numeric text, the cost is NULL; a weight written as text ('2.5') is read as a number.
- sku_check: Whenever a code made only of digits is given, the result is the same code with one Luhn (mod-10) check digit appended ('7992739871' gives '79927398713').
- sku_check: Whenever the code is given as a number rather than text, it is treated as its digits (79927398713 gives '799273987138'), and the result is always text.
- sku_check: Whenever the code has leading zeros, they are kept ('007' gives '0075', '0' gives '00').
- sku_check: Whenever the code has spaces at the start or end, they are removed first (' 1234 ' gives '12344'); spaces inside the code ('12 34') make the result NULL.
- sku_check: Whenever the code is NULL, empty, contains any letter or symbol (minus or plus sign, decimal point), or contains non-ASCII digits, the result is NULL.
- sku_check: Whenever the code is a decimal number such as 12.0 or 1.5 (not text), the result is NULL.
- time_slot: Whenever a duration in minutes is given, it is rounded up to the next multiple of 15 minutes (1 gives 15, 15 stays 15, 16 gives 30, 46 gives 60), and exact multiples are unchanged.
- time_slot: Whenever the duration is 0 or negative, the result is 0.
- time_slot: Whenever the duration is fractional, it is rounded up too (0.1 gives 15, 14.5 gives 15, 15.01 gives 30).
- time_slot: Whenever the duration is NULL, empty text, or text that is not a number, the result is NULL; a number written as text ('30') is read as a number.
- workdays_between: Whenever two valid ISO dates (YYYY-MM-DD) are given and the end date is after the start date, the result is the number of working days from the start date up to but not including the end date. A working day is a Monday–Friday day that is not a weekday January 1 or December 25 (see rule 57). Example: 2024-01-01 (Monday) to 2024-01-08 gives 5, to 2024-01-05 gives 4. If the end date is on or before the start date, the result is 0 (see rule 56).
- workdays_between: Whenever the end date itself is a working day, it is not counted, and the start date is counted if it is a working day (2024-01-05 Friday to 2024-01-06 gives 1; 2024-01-06 to 2024-01-08 gives 0).
- workdays_between: Whenever the start and end are the same day, or both fall on a weekend, the result is 0.
- workdays_between: Whenever the end date is on or before the start date (including a reversed range, such as 2026-11-09 to 2026-11-02), the result is 0. The result is never negative, however far apart the dates are, and the weekdays between the two dates are not counted backwards.
- workdays_between: Saturdays and Sundays are never counted. January 1 (New Year's Day) and December 25 (Christmas Day) are not counted in any year when they fall on a weekday, whether they are the start date or fall inside the range (the end date is never counted anyway). Every other public holiday that falls on a weekday is still counted as an ordinary working day; no other holidays are excluded. Example: 2026-12-24 (Thursday) to 2027-01-04 gives 5, because 2026-12-25 and 2027-01-01 are not counted.
- workdays_between: Whenever a date is NULL, empty, not exactly 10 characters, not in YYYY-MM-DD form (e.g. '2024-1-1', '2024/01/01', '20240101', a date with a time), not a real calendar date (2024-02-30) or a number, the result is NULL.
- workdays_between: Whenever a date has spaces around it (' 2024-01-01 '), the spaces are ignored and the date is accepted.
- clean_avg: Whenever it is applied to a set of rows, the result is the plain average of the values that are numbers, ignoring the others; example 10, 20, NULL, 35 gives 21.67.
- clean_avg: Whenever a row is NULL, empty text, text that is not a number ('n/a'), or binary data, it is skipped and does not count in the number of rows divided by.
- clean_avg: Whenever a value is a number written as text ('20', ' 4 ', '1e2'), it is read as a number and included.
- clean_avg: Whenever there are no rows at all (for example, a day with no orders), or no row holds a usable number, the result is 0.0, never blank or NULL and never an error. This includes the case where every row is skipped or excluded, such as when the only entries are junk text like 'abc', 'n/a', empty text, NULL, binary data, negative values, or values above 10000. With groups, a group with no usable number also gets 0.0. It is returned as a decimal number, so it shows as 0.0.
- clean_avg: Values that are negative are excluded. Zero is kept and included like any other number. Values above 10000 are excluded.
- clean_avg: Whenever the result is calculated, it is not rounded (e.g. 2.1666666666666665); it is returned as a decimal number, and with groups each group gets its own average.
- clean_avg: Whenever a text value reads as 'inf' or 'nan', it is treated as a number and makes the average infinite or not-a-number.
- A customer with no name on file gets no badge at all (blank). The owner says: Case 5 matches my policy, so nothing jumps out at me.

ENTER
- A 10,000-rupee invoice that is 30 days late already reaches the 1,500-rupee ceiling, so day 31 or day 90 adds nothing more. The owner says: That's wrong. 30 days late is 15%, which is 1,500, but the cap is 25% (2,500), so it keeps growing until day 50.
- A 2 kg parcel sent to a zone D, which does not exist, gets no price at all (blank) rather than an error. The owner says: It should be billed as zone C, so 16.06, not blank.
