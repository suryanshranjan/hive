import pathlib
D = pathlib.Path(__file__).parent
page = lambda n: (D / n).read_text(encoding='utf-8')
def test_pages_exist():
    for n in ('index.html', 'signup.html', 'dashboard.html', 'deals.html', 'invite.html', 'terms.html'):
        assert (D / n).exists()
def test_signup_collects_email_and_instagram():
    s = page('signup.html'); assert 'name="email"' in s and 'name="instagram"' in s
def test_signup_goes_to_dashboard():
    assert 'dashboard.html' in page('signup.html')
def test_deals_listed():
    assert page('deals.html').count('<li') >= 3
def test_invite_reward_is_500():
    assert '₹500' in page('invite.html')
def test_signup_is_short():
    s = page('signup.html')
    for n in ('pan', 'gst', 'account', 'ifsc', 'address'):
        assert f'name="{n}"' not in s
    assert s.count('required') <= 4
def test_signup_phone_number_keypad_and_payout_note():
    s = page('signup.html')
    assert 'inputmode="tel"' in s
    assert 'Join Sunny Shop' in s and 'See deals' in s
    assert "You'll add PAN and bank details only when you get paid for your first deal." in s
def test_dashboard_shows_deals():
    s = page('dashboard.html')
    assert 'deals.html' in s and 'No data.' not in s
    assert 'Pick your first deal' in s and 'See all open deals' in s
    assert s.count('>Apply</a>') == 3 and '<title>Dashboard</title>' in s
    for brand in ('Chai Co', 'Kurta House', 'FitBottle'):
        assert brand in s
def test_nav_links_to_deals():
    for n in ('dashboard.html', 'deals.html'):
        assert '<a href="deals.html">Deals</a>' in page(n)
def test_apply_goes_to_applied_page():
    assert (D / 'applied.html').exists()
    d = page('deals.html')
    assert d.count('applied.html') >= 3 and d.count('<li') >= 3 and '<button>Apply</button>' not in d
    for slug in ('chai-co', 'kurta-house', 'fitbottle'):
        assert f'applied.html?deal={slug}' in d
def test_applied_page_explains_next_steps():
    s = page('applied.html')
    assert "You've applied!" in s and '7 days' in s and 'your deal' in s
    assert s.count('<li') >= 3 and 'style.css' in s
    assert '<a href="deals.html">Apply to another deal</a>' in s
    assert '<a href="deals.html">Deals</a>' in s
def test_home_pitches_creators_with_signup_above_footer():
    s = page('index.html')
    assert s.count('signup.html') >= 2 and '₹' in s
    assert 'signup.html' in s.split('<footer')[0]
    assert 'Get paid by Indian brands for your Instagram posts' in s
    assert 'Creators earn ₹8,000/month on average' in s
    assert 'Join free' in s and s.index('Join free') < s.index('About us') < s.index('Brands')
