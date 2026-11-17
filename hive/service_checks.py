"""Live connection checks that never send mail, create events or message Telegram."""
import argparse
import json


def check(repo='.', live=False):
    from . import google, telegram
    cfg = google._load()
    bot = telegram.load()
    result = {'google': 'configured' if cfg.get('refresh_token') else 'not_configured',
              'telegram': 'configured' if bot else 'not_configured', 'live_reads': live}
    if not live:
        return result
    if result['google'] == 'configured':
        for name, scope, endpoint in (
            ('gmail', 'gmail', 'https://gmail.googleapis.com/gmail/v1/users/me/profile'),
            ('calendar', 'calendar', 'https://www.googleapis.com/calendar/v3/users/me/calendarList?maxResults=1'),
        ):
            if not google.connected(scope):
                result[name] = 'scope_not_connected'; continue
            try:
                google.call('GET', endpoint, retry=False)
                result[name] = 'live_read_passed'
            except Exception as exc:
                result[name] = 'failed:' + type(exc).__name__
    if bot:
        try:
            telegram._call(bot['token'], 'getMe')
            result['telegram'] = 'live_read_passed'
        except Exception as exc:
            result['telegram'] = 'failed:' + type(exc).__name__
    return result


def main(argv):
    parser = argparse.ArgumentParser(prog='hive verify-services')
    parser.add_argument('--live-read-only', action='store_true')
    args = parser.parse_args(argv)
    result = check(live=args.live_read_only)
    print(json.dumps(result, indent=2))
    if args.live_read_only:
        return int(any(value in ('not_configured', 'scope_not_connected') or str(value).startswith('failed:')
                       for value in result.values()))
    return 0
