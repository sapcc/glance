Verify operation
~~~~~~~~~~~~~~~~

Verify operation of the Image service using
`CirrOS <http://launchpad.net/cirros>`__, a small
Linux image that helps you test your OpenStack deployment.

For more information about how to download and build images, see
`OpenStack Virtual Machine Image Guide
<https://docs.openstack.org/image-guide/>`__.
For information about how to manage images, see the
`OpenStack End User Guide
<https://docs.openstack.org/user-guide/common/cli-manage-images.html>`__.

.. note::

   Perform these commands on the controller node.

#. Source the ``admin`` credentials to gain access to
   admin-only CLI commands:

   .. code-block:: console

      $ . admin-openrc

   .. end

#. Download the source image:

   .. code-block:: console

      $ wget http://download.cirros-cloud.net/0.4.0/cirros-0.4.0-x86_64-disk.img

   .. end

   .. note::

      Install ``wget`` if your distribution does not include it.

#. Upload the image to the Image service using the
   :term:`QCOW2 <QEMU Copy On Write 2 (QCOW2)>` disk format, :term:`bare`
   container format, and public visibility so all projects can access it:

   .. code-block:: console

      $ openstack image create "cirros" \
        --file cirros-0.4.0-x86_64-disk.img \
        --disk-format qcow2 --container-format bare \
        --public

      +------------------+------------------------------------------------------+
      | Field            | Value                                                |
      +------------------+------------------------------------------------------+
      | checksum         | 133eae9fb1c98f45894a4e60d8736619                     |
      | container_format | bare                                                 |
      | created_at       | 2015-03-26T16:52:10Z                                 |
      | disk_format      | qcow2                                                |
      | file             | /v2/images/cc5c6982-4910-471e-b864-1098015901b5/file |
      | id               | cc5c6982-4910-471e-b864-1098015901b5                 |
      | min_disk         | 0                                                    |
      | min_ram          | 0                                                    |
      | name             | cirros                                               |
      | owner            | ae7a98326b9c455588edd2656d723b9d                     |
      | protected        | False                                                |
      | schema           | /v2/schemas/image                                    |
      | size             | 13200896                                             |
      | status           | active                                               |
      | tags             |                                                      |
      | updated_at       | 2015-03-26T16:52:10Z                                 |
      | virtual_size     | None                                                 |
      | visibility       | public                                               |
      +------------------+------------------------------------------------------+

   .. end

   For information about the :command:`openstack image create` parameters,
   see `Create or update an image (glance)
   <https://docs.openstack.org/user-guide/common/cli-manage-images.html#create-or-update-an-image-glance>`__
   in the ``OpenStack User Guide``.

   For information about disk and container formats for images, see
   `Disk and container formats for images
   <https://docs.openstack.org/image-guide/image-formats.html>`__
   in the ``OpenStack Virtual Machine Image Guide``.

   .. note::

      OpenStack generates IDs dynamically, so you will see
      different values in the example command output.

#. Confirm upload of the image and validate attributes:

   .. code-block:: console

      $ openstack image list

      +--------------------------------------+--------+--------+
      | ID                                   | Name   | Status |
      +--------------------------------------+--------+--------+
      | 38047887-61a7-41ea-9b49-27987d5e8bb9 | cirros | active |
      +--------------------------------------+--------+--------+

   .. end
