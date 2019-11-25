..
      Copyright 2010 OpenStack Foundation
      All Rights Reserved.

      Licensed under the Apache License, Version 2.0 (the "License"); you may
      not use this file except in compliance with the License. You may obtain
      a copy of the License at

          http://www.apache.org/licenses/LICENSE-2.0

      Unless required by applicable law or agreed to in writing, software
      distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
      WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
      License for the specific language governing permissions and limitations
      under the License.

==================================
Welcome to Glance's documentation!
==================================

About Glance
============

The Image service (glance) project provides a service where users can upload
and discover data assets that are meant to be used with other services.
This currently includes images and metadata definitions.

Glance image services include discovering, registering, and
retrieving virtual machine (VM) images. Glance has a RESTful API that allows
querying of VM image metadata as well as retrieval of the actual image.

.. include:: deprecation-note.inc

VM images made available through Glance can be stored in a variety of
locations from simple filesystems to object-storage systems like the
OpenStack Swift project.

Glance, as with all OpenStack projects, is written with the following design
guidelines in mind:

* **Component based architecture**: Quickly add new behaviors
* **Highly available**: Scale to very serious workloads
* **Fault tolerant**: Isolated processes avoid cascading failures
* **Recoverable**: Failures should be easy to diagnose, debug, and rectify
* **Open standards**: Be a reference implementation for a community-driven api

Glance Documentation
====================

The Glance Project Team has put together the following documentation for you.
Pick the documents that best match your user profile.

.. list-table::
   :header-rows: 1

   * - User Profile
     - Links
   * - | **Contributor**
       | You want to contribute code, documentation, reviews, or
         ideas to the Glance Project.
     - * :doc:`contributor/index`
   * - | **Administrator**
       | You want to administer and maintain a Glance installation.
     - * :doc:`admin/index`
       * :doc:`cli/index`
   * - | **Operator**
       | You want to install and configure Glance for your cloud.
     - * :doc:`install/index`
       * :doc:`configuration/index`
   * - | **End User** or **Third-party Developer**
       | You want to use the Image Service APIs provided by Glance.
     - * `Image Service API Reference <https://developer.openstack.org/api-ref/image/>`_
       * `Image Service API Guide <https://specs.openstack.org/openstack/glance-specs/specs/api/v2/image-api-v2.html>`_
       * :doc:`user/index`
   * - **Everyone**
     - Here's a handy :doc:`glossary` of terms related to Glance

.. toctree::
   :hidden:

   contributor/index
   admin/index
   cli/index
   install/index
   configuration/index
   user/index
   glossary
