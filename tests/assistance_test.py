from datetime import datetime
import usaspending.usaspending_assistance as assistance

def test_archive_date():
    """Test latest bulk file dates on USAspending."""
    test_date = assistance.get_archive_date()
    d = datetime.strptime(test_date, '%Y%M%d')
    assert type(d) == datetime
    assert datetime(2014, 1, 1) <= d <= datetime.now()



