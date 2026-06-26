import { AUTHORITY, hasAuthority } from "./auth";
import type { AuthInfo } from "./types";

export type FeatureId = "assistant" | "reports" | "crawler";

export type FeatureDefinition = {
  id: FeatureId;
  label: string;
  hint: string;
  authority: string;
};

/** Embed-ready feature registry — host shell can mirror this map later. */
export const FEATURES: FeatureDefinition[] = [
  {
    id: "assistant",
    label: "Assistant",
    hint: "Ask questions grounded in procurement data",
    authority: AUTHORITY.AI_READ,
  },
  {
    id: "reports",
    label: "Reports",
    hint: "Structured spend, vendor, and entity reports",
    authority: AUTHORITY.REPORT_READ,
  },
  {
    id: "crawler",
    label: "Crawler",
    hint: "Scan datasets for alerts and anomalies",
    authority: AUTHORITY.CRAWLER_READ,
  },
];

export function accessibleFeatures(user: AuthInfo): FeatureDefinition[] {
  return FEATURES.filter((feature) => hasAuthority(user, feature.authority));
}

export function canAccessFeature(user: AuthInfo, featureId: FeatureId): boolean {
  const feature = FEATURES.find((f) => f.id === featureId);
  return feature ? hasAuthority(user, feature.authority) : false;
}

export function defaultFeature(user: AuthInfo): FeatureId {
  return accessibleFeatures(user)[0]?.id ?? "assistant";
}
