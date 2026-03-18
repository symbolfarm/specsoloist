# Internals Reference

This page documents SpecSoloist's internal modules. It is intended for contributors
and agents working on the framework itself, not for library users.

For the public-facing API, see [Public API](api.md).

---

## Parser

::: specsoloist.parser.SpecParser

::: specsoloist.parser.ParsedSpec

::: specsoloist.parser.SpecMetadata

---

## Compiler

::: specsoloist.compiler.SpecCompiler

---

## Runner

::: specsoloist.runner.TestRunner

::: specsoloist.runner.TestResult

---

## Dependency Resolver

::: specsoloist.resolver.DependencyResolver

::: specsoloist.resolver.DependencyGraph

::: specsoloist.resolver.CircularDependencyError

::: specsoloist.resolver.MissingDependencyError

---

## Build Manifest

::: specsoloist.manifest.BuildManifest

::: specsoloist.manifest.IncrementalBuilder

::: specsoloist.manifest.SpecBuildInfo

---

## Spec Drift Detection

::: specsoloist.spec_diff.SpecDiffResult

::: specsoloist.spec_diff.SpecDiffIssue

---

## Respec

::: specsoloist.respec.Respecer
