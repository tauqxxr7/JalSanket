from scripts.evaluate import summarize


def test_metrics_count_abstentions_without_inventing_negative_results():
    cases=[{'injected':True,'outcome':'FLAG','latency_hours':6},
           {'injected':True,'outcome':None,'latency_hours':None},
           {'injected':False,'outcome':'FLAG','latency_hours':None},
           {'injected':False,'outcome':'NO_FLAG','latency_hours':None},
           {'injected':False,'outcome':None,'latency_hours':None}]
    metrics=summarize(cases)
    assert metrics['precision']==.5
    assert metrics['recall']==.5
    assert metrics['f1']==.5
    assert metrics['false_positive_rate_on_executed_unmodified_controls']==.5
    assert metrics['execution_coverage']==.6
    assert metrics['median_detection_latency_source_hours']==6


def test_undefined_metrics_are_null_not_perfect_scores():
    metrics=summarize([])
    assert metrics['precision'] is None
    assert metrics['false_positive_rate_on_executed_unmodified_controls'] is None
    assert metrics['median_detection_latency_source_hours'] is None
