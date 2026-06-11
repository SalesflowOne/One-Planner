# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only

from rest_framework import serializers

from plane.oneplan.models import Constraint, ConstraintIssueLink, Objective, Pillar


class PillarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pillar
        fields = "__all__"
        read_only_fields = ["workspace", "created_by", "updated_by", "created_at", "updated_at"]


class ObjectiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Objective
        fields = "__all__"
        read_only_fields = ["workspace", "created_by", "updated_by", "created_at", "updated_at"]


class ConstraintSerializer(serializers.ModelSerializer):
    linked_issue_ids = serializers.SerializerMethodField()

    class Meta:
        model = Constraint
        fields = "__all__"
        read_only_fields = ["workspace", "created_by", "updated_by", "created_at", "updated_at"]

    def get_linked_issue_ids(self, obj):
        return list(
            ConstraintIssueLink.objects.filter(constraint=obj).values_list("issue_id", flat=True)
        )


class ConstraintIssueLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConstraintIssueLink
        fields = "__all__"
        read_only_fields = ["created_by", "updated_by", "created_at", "updated_at"]
