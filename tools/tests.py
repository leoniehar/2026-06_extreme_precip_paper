def KS_test_distributions(ref, comp, alpha = 0.05):
    import numpy as np
    from scipy.stats import ks_2samp
    ''' 
    Kolmogorow-Smirnow-Test
    https://www.geeksforgeeks.org/machine-learning/kolmogorov-smirnov-test-ks-test/
    '''
    
    np.random.seed(42)
    
    for var in ref.data_vars:
        # Flatten and remove NaNs
        sample_land = ref[var].values.flatten()
        sample_ocean = comp[var].values.flatten()
        sample_land = sample_land[np.isfinite(sample_land)]
        sample_ocean = sample_ocean[np.isfinite(sample_ocean)]
        
        # KS test
        ks_stat, p_value = ks_2samp(sample_land, sample_ocean, alternative='two-sided', mode='auto')
        
        print(f"Variable: {var}")
        print(f"  KS Statistic: {ks_stat:.4f}")
        print(f"  P-value: {p_value:.4f}")
        
        if p_value < alpha:
            print("  -> Reject null hypothesis: distributions differ.\n")
        else:
            print("  -> Fail to reject null hypothesis: no significant difference.\n")
