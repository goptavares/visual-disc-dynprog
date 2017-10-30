#!/usr/bin/env python

"""
Copyright (C) 2017, California Institute of Technology

This file is part of addm_toolbox.

addm_toolbox is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

addm_toolbox is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with addm_toolbox. If not, see <http://www.gnu.org/licenses/>.

---

Module: ddm_pta_test.py
Author: Gabriela Tavares, gtavares@caltech.edu

Test to check the validity of the DDM parameter estimation. Artificial data is
generated using specific parameters for the model. These parameters are then
recovered through a maximum a posteriori estimation procedure.
"""

from __future__ import absolute_import, division

import pkg_resources

from builtins import range, str

from .ddm import DDMTrial, DDM
from .util import load_trial_conditions_from_csv


def main(d, sigma, rangeD, rangeSigma, trialsFileName=None,
         trialsPerCondition=800, numThreads=9, verbose=False):
    """
    Args:
      d: float, DDM parameter for generating artificial data.
      sigma: float, DDM parameter for generating artificial data.
      rangeD: list of floats, search range for parameter d.
      rangeSigma: list of floats, search range for parameter sigma.
      trialsFileName: string, path of trial conditions file.
      trialsPerCondition: int, number of artificial data trials to be
          generated per trial condition.
      numThreads: int, size of the thread pool.
      verbose: boolean, whether or not to increase output verbosity.
    """
    # Load trial conditions.
    if not trialsFileName:
        trialsFileName = pkg_resources.resource_filename(
            u"addm_toolbox", u"test_data/test_trial_conditions.csv")
    trialConditions = load_trial_conditions_from_csv(trialsFileName)

    # Generate artificial data.
    model = DDM(d, sigma)
    trials = list()
    for (valueLeft, valueRight) in trialConditions:
        for t in range(trialsPerCondition):
            try:
                trials.append(model.simulate_trial(valueLeft, valueRight))
            except:
                print(u"An exception occurred while generating artificial "
                      "trial " + str(t) + u" for condition (" +
                      str(valueLeft) + u", " + str(valueRight) + u").")
                raise

    # Get likelihoods for all models and all artificial trials.
    numModels = len(rangeD) * len(rangeSigma)
    likelihoods = dict()
    models = list()
    posteriors = dict()
    for d in rangeD:
        for sigma in rangeSigma:
            model = DDM(d, sigma)
            if verbose:
                print(u"Computing likelihoods for model " + str(model.params) +
                      u"...")
            try:
                likelihoods[model.params] = model.parallel_get_likelihoods(
                    trials, numThreads=numThreads)
            except:
                print(u"An exception occurred during the likelihood "
                      "computations for model " + str(model.params) + u".")
                raise
            models.append(model)
            posteriors[model.params] = 1 / numModels

    # Compute the posteriors.
    for t in range(len(trials)):
        # Get the denominator for normalizing the posteriors.
        denominator = 0
        for model in models:
            denominator += (posteriors[model.params] *
                            likelihoods[model.params][t])
        if denominator == 0:
            continue

        # Calculate the posteriors after this trial.
        for model in models:
            prior = posteriors[model.params]
            posteriors[model.params] = (likelihoods[model.params][t] *
                prior / denominator)

    if verbose:
        for model in models:
            print(u"P" + str(model.params) +  u" = " +
                  str(posteriors[model.params]))
        print(u"Sum: " + str(sum(list(posteriors.values()))))
