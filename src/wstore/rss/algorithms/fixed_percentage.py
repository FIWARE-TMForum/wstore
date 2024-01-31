from wstore.rss.algorithms.rss_algorithm import RSSAlgorithm
from django.forms.models import model_to_dict


class FixedPercentage(RSSAlgorithm):
    id = "FIXED_PERCENTAGE"
    name = "Fixed Percentage Algorithm"
    desc = "Distributes the revenue based on fixed percentages for each party"

    @classmethod
    def calculate_revenue_share(cls, rs_model, total_revenue):
        """
        args:
            rs_model (RSSModel): The model to use for calculating the revenue share.
            total_revenue (Decimal): The total ammount to divide.
        """
        result = model_to_dict(rs_model, fields=["providerId", "productClass", "stakeholders", "algorithmType"])
        result["aggregatorTotal"] = total_revenue * rs_model.aggregatorShare / 100
        result["providerTotal"] = total_revenue * rs_model.providerShare / 100
        for stakeholder in result["stakeholders"]:
            stakeholder["stakeholderTotal"] = total_revenue * stakeholder["stakeholderShare"] / 100
            stakeholder.pop("stakeholderShare", None)
        return result
