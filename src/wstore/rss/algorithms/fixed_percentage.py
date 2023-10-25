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
        result = model_to_dict(rs_model)
        result["aggregatorShare"] = total_revenue * result["aggregatorValue"] / 100
        result["ownerShare"] = total_revenue * result["ownerValue"] / 100
        for stakeholder in rs_model.stakeholders:
            stakeholder["stakeholderShare"] = total_revenue * stakeholder["stakeholderValue"] / 100
        return result
