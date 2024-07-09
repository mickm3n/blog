from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
)
import json
import re
import os

PATH_FILTER_PATTERNS = [
    re.compile("/blog/.+"),
    re.compile("/reading-notes/.+"),
    re.compile("/wisdom/.+/.+"),
    re.compile("/about/"),
    re.compile("/changelog/"),
]


def get_view_count_dict(property_id="278031395"):
    """Runs a simple report on a Google Analytics 4 property."""
    # Using a default constructor instructs the client to use the credentials
    # specified in GOOGLE_APPLICATION_CREDENTIALS environment variable.
    # Load the service account info from the environment variable
    service_account_info = json.loads(os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON"))

    # Create a client using the service account info
    client = BetaAnalyticsDataClient.from_service_account_info(service_account_info)

    view_count_dict = dict()

    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[Dimension(name="pagePath")],
        metrics=[Metric(name="screenPageViews")],
        date_ranges=[DateRange(start_date="2020-03-31", end_date="today")],
        limit=250000,
    )
    response = client.run_report(request)

    for row in response.rows:
        dimension = row.dimension_values[0].value
        metric = row.metric_values[0].value
        if any([pattern.match(dimension) for pattern in PATH_FILTER_PATTERNS]):
            view_count_dict[dimension] = metric

    return view_count_dict


if __name__ == "__main__":
    view_count_dict = get_view_count_dict()
    with open("static/data/view_counts.json", "w") as wf:
        json.dump(view_count_dict, wf)
