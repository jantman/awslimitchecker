
.. _iam_policy:

Required IAM Permissions
========================

Below is the sample IAM policy from this version of awslimitchecker, listing the IAM
permissions required for it to function correctly:

.. code-block:: json

    {
      "Statement": [
        {
          "Action": [
            "ec2:DescribeInstances", 
            "ec2:DescribeReservedInstances", 
            "ec2:DescribeSecurityGroups", 
            "ec2:DescribeVolumes"
          ], 
          "Effect": "Allow", 
          "Resource": "*"
        }
      ], 
      "Version": "2012-10-17"
    }

