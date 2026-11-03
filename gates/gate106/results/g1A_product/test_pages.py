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
    assert s.count('<input') <= 4
    for f in ('gst', 'pan', 'account', 'ifsc', 'address'):
        assert f'name="{f}"' not in s
def test_home_invites_creators():
    s = page('index.html')
    assert s.count('href="signup.html"') >= 2 and '₹3,000' in s
    assert '₹8,000 a month on average' in s
def test_invite_reward_visible():
    s = page('invite.html')
    assert s.index('₹500') < s.index('<button') and 'margin-top:400px' not in s
def test_dashboard_links_next_steps():
    s = page('dashboard.html'); assert 'deals.html' in s and 'invite.html' in s
