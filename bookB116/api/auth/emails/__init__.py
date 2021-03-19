from bookB116.email import send_email, get_template


def send_vercode(stu_id: str, vercode: str, system_name: str):
    tmpl = get_template(__file__, 'vercode.html')
    msg = tmpl.render(vercode=vercode, system_name=system_name)
    if stu_id[0] > '1':
        email_addr = '%s@stu.pku.edu.cn' % stu_id
    else:
        email_addr = '%s@pku.edu.cn' % stu_id
    send_email(email_addr, '验证码', msg)
