import logging

from ocs_ci.ocs import ocp, constants
from ocs_ci.ocs.exceptions import ResourceNotFoundError, CommandFailed
from ocs_ci.ocs.node import get_node_objs
from ocs_ci.ocs.resources.pvc import get_all_pvcs_in_storageclass
from ocs_ci.ocs.uninstall import uninstall_ocs
from ocs_ci.utility.localstorage import check_local_volume
from tests.helpers import get_all_pvs

log = logging.getLogger(__name__)


def test_uninstall():
    """
    Test to validate all OCS resources were removed from cluster

    """
    # uninstall OCS if still exists -V
    csv_obj = ocp.OCP(namespace='openshift-storage', kind='', resource_name='csv')
    if csv_obj.is_exist():
        log.info("OCS will be uninstalled")
        uninstall_ocs()

    # checking for OCS storage classes - V
    ocs_sc_list = ['ocs-storagecluster-ceph-rbd',
                   'ocs-storagecluster-cephfs',
                   'ocs-storagecluster-ceph-rgw',
                   'openshift-storage.noobaa.io'
                   ]
    sc_obj = ocp.OCP(kind=constants.STORAGECLASS)
    for sc in ocs_sc_list:
        assert not sc_obj.is_exist(resource_name=sc), f"storage class {sc} was not deleted"

    # checking for OCS PVCs -V
    pvc_list = []
    for sc in ocs_sc_list:
        pvc_list.extend(get_all_pvcs_in_storageclass(sc))
    assert len(pvc_list) == 0, f"OCS PVCs were not deleted {[pvc.name for pvc in pvc_list]}"

    # checking for monitoring map -V
    monitoring_obj = ocp.OCP(
        namespace=constants.MONITORING_NAMESPACE,
        kind='ConfigMap',
        resource_name='cluster-monitoring-config',
    )
    assert monitoring_obj.get().get('data').get('config.yaml') is not None, \
        "OCS was not removed from monitoring stack"

    # checking for registry map - V
    image_registry_obj = ocp.OCP(
        kind=constants.IMAGE_REGISTRY_CONFIG, namespace=constants.OPENSHIFT_IMAGE_REGISTRY_NAMESPACE
    )
    assert 'pvc' not in image_registry_obj.get().get('spec').get('storage'), "OCS was not removed from regitry map"

    # checking for cluster logging object
    clusterlogging_obj = ocp.OCP(
        kind=constants.CLUSTER_LOGGING, namespace=constants.OPENSHIFT_LOGGING_NAMESPACE
    )

    assert not clusterlogging_obj.is_exist(), "cluster logging object was not deleted"  # checking for bucket classes

    # checking for backing store

    # checking for local volume - V
    assert not check_local_volume(), "local volume was not deleted"

    # checking for storage cluster - V
    storage_cluster = ocp.OCP(
        kind=constants.STORAGECLUSTER,
        resource_name=constants.DEFAULT_CLUSTERNAME,
        namespace='openshift-storage'
    )

    assert not storage_cluster.is_exist(resource_name=constants.DEFAULT_CLUSTERNAME), "storage cluster was not deleted"

    # checking for openshift-storage namespace -V
    openshift_storage_namespace = ocp.OCP(
        kind=constants.NAMESPACE,
        namespace='openshift-storage'
    )

    assert not openshift_storage_namespace.is_exist(resource_name='openshift-storage'), \
        "openshift-storage namespace was not deleted "

    # checking for PVs
    pvc_list = get_all_pvs()
    for pv in pvc_list:
        assert 'ocs-storagecluster-ceph-rbd|' or 'ocs-storagecluster-cephfs' in pv.get(
            'name'), f"OCS pv {pv.get('name')} was not deleted "

    # checking for LSO artifacts on nodes
    ocp_obj = ocp.OCP()
    nodes_list = get_node_objs()
    for node in nodes_list:
        try:
            assert not ocp_obj.exec_oc_debug_cmd(
                node=node, cmd_list=["ls -l /var/lib/rook"]), "OCS artificats were not deleted from nodes "
        except CommandFailed:
            pass

    # checking for rook artificats on nodes
    for node in nodes_list:
        try:
            assert not ocp_obj.exec_oc_debug_cmd(node=node, cmd_list=["ls -l /mnt/local-storage/local-block"]), \
                "LSO artificats were not deleted from nodes "
        except CommandFailed:
            pass

    # checking for labels on nodes - v
    for node in nodes_list:
        labels = node.get().get('metadata').get('labels')
        print(labels)
        assert constants.OPERATOR_NODE_LABEL in labels, f"OCS labels was not removed from {node} node"

    # checking for CRDs
    crds = ['backingstores.noobaa.io', 'bucketclasses.noobaa.io', 'cephblockpools.ceph.rook.io',
            'cephfilesystems.ceph.rook.io', 'cephnfses.ceph.rook.io',
            'cephobjectstores.ceph.rook.io', 'cephobjectstoreusers.ceph.rook.io', 'noobaas.noobaa.io',
            'ocsinitializations.ocs.openshift.io', 'storageclusterinitializations.ocs.openshift.io',
            'storageclusters.ocs.openshift.io', 'cephclusters.ceph.rook.io']
    for crd in crds:
        try:
            ocp_obj.exec_oc_cmd(f'get crd {crd}')
        except ResourceNotFoundError:
            pass
