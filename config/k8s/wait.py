#!/usr/bin/env -S python3 -u

import sys
import time
import argparse
from kubernetes import client, config
from pprint import pprint


def job_show(job):
    print("Succeeded:", job.status.succeeded)
    print("Failed:", job.status.failed)
    if job.status.conditions:
        for cond in job.status.conditions:
            print("condition.type:", cond.type)


def job_succeeded(job):
    return job.status.succeeded == True


def context_valid(c):
    valid = False

    print("Available contexts:")
    contexts, active_context = config.list_kube_config_contexts()
    for ctx in contexts:
        print("   {}".format(ctx['name']))
        if c == ctx['name']:
            valid = True

    return valid


def main(args):
    build_success = True
    k8s_success = True
    job_found = False
    sleep_secs = args.sleep
    deadline_timestamp = time.time() + args.timeout

    if not context_valid(args.context):
        print("ERROR: unknown context", args.context)
        sys.exit(1)

    retries = 3
    print("Using context:", args.context)
    while retries:
        try:
            config.load_kube_config(context=args.context)
            break
        except (TypeError, config.ConfigException) as e:
            print("WARNING: unable to load context {}: {}.  Retrying.".format(args.context, e))
            time.sleep(sleep_secs)
            retries = retries - 1
    if retries == 0:
        print("ERROR: unable to load context {}.  Giving up.".format(args.context))
        sys.exit(1)

    print(f'Waiting for job completion. (recheck every {sleep_secs} sec,'
          f'timeout {args.timeout})')

    #
    # wait for job to finish
    #
    retries = 3  # max API failure retries
    batch = client.BatchV1Api()
    while retries:
        job_found = False
        try:
            job = batch.read_namespaced_job(name=args.job_name,
                                            namespace=args.namespace)
        except client.rest.ApiException as e:
            print("x:", e)
            time.sleep(sleep_secs)
            retries = retries - 1
            sleep_secs = sleep_secs * 2
            continue

        job_found = True
        if job.status.active or not job.status.conditions:
            if time.time() > deadline_timestamp:
                print("Deadline exceed")
            else:
                print(".")
                time.sleep(sleep_secs)
                continue

        build_success = job_succeeded(job)
        if build_success:
            print("PASS")
        else:
            print("FAIL")
            if job.status.conditions:
                print("Reason:", job.status.conditions[0].reason)
            else:
                print("Reason: Unknown: job status:")
                pprint(job.status)

        break

    if not job_found:
        print("ERROR: unable to find job {}".format(args.job_name))
        sys.exit(1)

    #
    # Find pod where job ran
    #
    core = client.CoreV1Api()
    pod = core.list_namespaced_pod(namespace=args.namespace, watch=False,
                                   label_selector="job-name={}".format(args.job_name))
    if len(pod.items) < 1:
        print("WARNING: no pods found with job name {}".format(args.job_name))
        sys.exit(0)
    if len(pod.items) > 1:
        print("WARNING: >1 pod found with job name {}".format(args.job_name))
        sys.exit(0)
    pod_name = pod.items[0].metadata.name
    print("Found job on pod {}".format(pod_name))

    #
    # Get logs (from pod)
    #

    # default: check the main container logs
    cont_name = pod.items[0].spec.containers[0].name

    # unless the initContainer failed, get that log, because if the
    # initContainer failed, the main container will not have run
    if (pod.items[0].spec.init_containers):
        init_cont_name = pod.items[0].spec.init_containers[0].name
        if pod.items[0].status.init_container_statuses is not None\
            and not pod.items[0].status.init_container_statuses[0].ready:
            print("ERROR: initContainer {} not ready / failed.".format(init_cont_name))
            cont_name = init_cont_name
            k8s_success = False
    try:
        log = core.read_namespaced_pod_log(name=pod_name,
                                           namespace=args.namespace,
                                           container=cont_name)
        print("Container Log:")
        print(log)
    except client.rest.ApiException as e:
        print("Exception: Unable to get pod log", e)
        k8s_success = False

    #
    # Delete job
    #
    if args.delete and k8s_success:
        # important: propagation_policy is important so any pods
        # created for a job deleted
        body = client.V1DeleteOptions(propagation_policy="Foreground")
        ret = batch.delete_namespaced_job(name=args.job_name,
                                          namespace=args.namespace,
                                          body=body)
        print("job {} deleted.  job.status:".format(args.job_name))
        pprint(ret.status)

    # Make jenkins fail only if k8s fails.  Kernel build fails will
    # be reported to the backend/
    sys.exit(not k8s_success)
 

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--context')
    parser.add_argument('--job-name')
    parser.add_argument('--namespace', default='default')
    parser.add_argument('--sleep', type=int, default=60)
    # Default timeout 42 minutes as Jenkins timeout is 45 minutes
    parser.add_argument('--timeout', type=int, default=2520)
    parser.add_argument('--no-delete', dest='delete', default=True, action='store_false')
    args = parser.parse_args()
    main(args)
