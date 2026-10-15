"""Reserved for V2: free-text meal parsing ("2 ouă și o felie de pâine").

Not implemented in V1. The router is mounted only when FEATURE_AI_MEAL_PARSING=true and
answers 501 until an implementation of `MealParser` exists. Nothing else imports this
package, so V1 behaviour is fully deterministic.
"""
