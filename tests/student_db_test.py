from bookB116.database import Student

from . import RAW_STU_IDS


# Magical param `client`
# It seems that pytest won't do fixture stuff when
# there is not client param, and there will be errors
# either saying the is no such table or context error
def test_build_success(client):
    '''Test if we have built database correctly from the data file'''
    for stu_id in RAW_STU_IDS:
        assert Student.by_raw_id(stu_id)
