import { useEffect, useRef } from "react";
import { createPortal } from "react-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { X, AlertCircle, Sparkles, HelpCircle } from "lucide-react";
import { cn } from "../lib/utils";
import type { Report, CreateRequestPayload } from "../types";

// Validation schema
const requestSchema = z.object({
  requester_email: z.string().email("Please enter a valid email address"),
  title: z.string().min(5, "Title must be at least 5 characters"),
  description: z.string().min(10, "Description must be at least 10 characters"),
  request_type: z.enum(["issue", "enhancement", "other"], {
    message: "Please select a request type",
  }),
  priority: z.enum(["low", "medium", "high"], {
    message: "Please select a priority",
  }),
});

type RequestFormData = z.infer<typeof requestSchema>;

// Request type configuration for visual buttons
const requestTypeConfig = [
  { value: "issue", label: "Issue", description: "Something isn't working or data is incorrect", icon: AlertCircle, color: "red" },
  { value: "enhancement", label: "Enhancement", description: "Add or improve a feature", icon: Sparkles, color: "purple" },
  { value: "other", label: "Other", description: "General request", icon: HelpCircle, color: "gray" },
] as const;

interface RequestModalProps {
  isOpen: boolean;
  onClose: () => void;
  report: Report | null;
  onSubmit: (data: CreateRequestPayload) => Promise<void>;
  isSubmitting: boolean;
}

export function RequestModal({
  isOpen,
  onClose,
  report,
  onSubmit,
  isSubmitting,
}: RequestModalProps) {
  const modalRef = useRef<HTMLDivElement>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<RequestFormData>({
    resolver: zodResolver(requestSchema),
    defaultValues: {
      requester_email: "",
      title: "",
      description: "",
      request_type: undefined,
      priority: "medium",
    },
  });

  // Reset form when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      reset();
    }
  }, [isOpen, reset]);

  // Focus trap
  useEffect(() => {
    if (!isOpen) return;

    const focusableElements = modalRef.current?.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const firstElement = focusableElements?.[0] as HTMLElement;
    const lastElement = focusableElements?.[focusableElements.length - 1] as HTMLElement;

    firstElement?.focus();

    const handleTab = (e: KeyboardEvent) => {
      if (e.key !== "Tab") return;

      if (e.shiftKey && document.activeElement === firstElement) {
        e.preventDefault();
        lastElement?.focus();
      } else if (!e.shiftKey && document.activeElement === lastElement) {
        e.preventDefault();
        firstElement?.focus();
      }
    };

    document.addEventListener("keydown", handleTab);
    return () => document.removeEventListener("keydown", handleTab);
  }, [isOpen]);

  // Escape to close
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !isSubmitting) onClose();
    };

    if (isOpen) {
      document.addEventListener("keydown", handleEscape);
      document.body.style.overflow = "hidden";
    }

    return () => {
      document.removeEventListener("keydown", handleEscape);
      document.body.style.overflow = "";
    };
  }, [isOpen, onClose, isSubmitting]);

  const handleFormSubmit = async (data: RequestFormData) => {
    if (!report) return;

    await onSubmit({
      report_id: report.id,
      report_name: report.name,
      title: data.title,
      description: data.description,
      request_type: data.request_type,
      priority: data.priority,
      requester_email: data.requester_email,
    });
  };

  if (!isOpen || !report) return null;

  return createPortal(
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50 animate-backdrop"
      onClick={() => !isSubmitting && onClose()}
    >
      {/* P3.2 - Modal animation, P4.2 - Mobile responsive width */}
      <div
        ref={modalRef}
        className="bg-white rounded-xl w-full max-w-lg mx-4 md:mx-0 p-4 md:p-6 max-h-[90vh] overflow-y-auto animate-modal-in"
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex justify-between items-start mb-6">
          <div>
            <h2 id="modal-title" className="text-xl font-semibold text-gray-900">
              Request Change
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              for {report.name}
            </p>
          </div>
          <button
            onClick={onClose}
            disabled={isSubmitting}
            className="text-gray-400 hover:text-gray-600 disabled:opacity-50 transition-colors duration-200"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" aria-hidden="true" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
          {/* Email */}
          <div>
            <label htmlFor="requester_email" className="block text-sm font-medium text-gray-700 mb-1">
              Your Email <span className="text-red-500">*</span>
            </label>
            <input
              id="requester_email"
              type="email"
              {...register("requester_email")}
              placeholder="your.email@company.com"
              className={cn(
                "w-full px-3 py-2 border rounded-lg text-sm",
                "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent",
                errors.requester_email ? "border-red-300" : "border-gray-300"
              )}
              disabled={isSubmitting}
            />
            {errors.requester_email && (
              <p className="text-red-500 text-sm mt-1">{errors.requester_email.message}</p>
            )}
          </div>

          {/* Title */}
          <div>
            <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-1">
              Title <span className="text-red-500">*</span>
            </label>
            <input
              id="title"
              {...register("title")}
              placeholder="Brief summary of the change request"
              className={cn(
                "w-full px-3 py-2 border rounded-lg text-sm",
                "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent",
                errors.title ? "border-red-300" : "border-gray-300"
              )}
              disabled={isSubmitting}
            />
            {errors.title && (
              <p className="text-red-500 text-sm mt-1">{errors.title.message}</p>
            )}
          </div>

          {/* Description */}
          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
              Description <span className="text-red-500">*</span>
            </label>
            <textarea
              id="description"
              {...register("description")}
              rows={4}
              placeholder="Describe the change you need in detail..."
              className={cn(
                "w-full px-3 py-2 border rounded-lg text-sm resize-none",
                "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent",
                errors.description ? "border-red-300" : "border-gray-300"
              )}
              disabled={isSubmitting}
            />
            {errors.description && (
              <p className="text-red-500 text-sm mt-1">{errors.description.message}</p>
            )}
          </div>

          {/* Request Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Request Type <span className="text-red-500">*</span>
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
              {requestTypeConfig.map((type) => {
                const Icon = type.icon;
                return (
                  <label
                    key={type.value}
                    className={cn(
                      "flex flex-col items-center gap-2 p-3 rounded-lg border cursor-pointer transition-colors text-center",
                      "has-[:checked]:border-2",
                      type.color === "red" && "has-[:checked]:border-red-500 has-[:checked]:bg-red-50",
                      type.color === "purple" && "has-[:checked]:border-purple-500 has-[:checked]:bg-purple-50",
                      type.color === "gray" && "has-[:checked]:border-gray-500 has-[:checked]:bg-gray-50",
                      isSubmitting && "opacity-50 cursor-not-allowed"
                    )}
                  >
                    <input
                      type="radio"
                      {...register("request_type")}
                      value={type.value}
                      className="sr-only"
                      disabled={isSubmitting}
                    />
                    <Icon className={cn(
                      "w-5 h-5",
                      type.color === "red" && "text-red-500",
                      type.color === "purple" && "text-purple-500",
                      type.color === "gray" && "text-gray-500"
                    )} aria-hidden="true" />
                    <div>
                      <span className="text-sm font-medium block">{type.label}</span>
                      <p className="text-xs text-gray-500">{type.description}</p>
                    </div>
                  </label>
                );
              })}
            </div>
            {errors.request_type && (
              <p className="text-red-500 text-sm mt-1">{errors.request_type.message}</p>
            )}
          </div>

          {/* Priority */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Priority <span className="text-red-500">*</span>
            </label>
            <div className="flex gap-4">
              {[
                { value: "low", label: "Low", color: "blue" },
                { value: "medium", label: "Medium", color: "yellow" },
                { value: "high", label: "High", color: "red" },
              ].map((option) => (
                <label
                  key={option.value}
                  className={cn(
                    "flex-1 flex items-center justify-center gap-2 py-2 px-3 rounded-lg border cursor-pointer transition-colors",
                    "has-[:checked]:border-2",
                    option.color === "blue" && "has-[:checked]:border-blue-500 has-[:checked]:bg-blue-50",
                    option.color === "yellow" && "has-[:checked]:border-yellow-500 has-[:checked]:bg-yellow-50",
                    option.color === "red" && "has-[:checked]:border-red-500 has-[:checked]:bg-red-50",
                    isSubmitting && "opacity-50 cursor-not-allowed"
                  )}
                >
                  <input
                    type="radio"
                    {...register("priority")}
                    value={option.value}
                    className="sr-only"
                    disabled={isSubmitting}
                  />
                  <span
                    className={cn(
                      "w-2 h-2 rounded-full",
                      option.color === "blue" && "bg-blue-500",
                      option.color === "yellow" && "bg-yellow-500",
                      option.color === "red" && "bg-red-500"
                    )}
                  />
                  <span className="text-sm font-medium">{option.label}</span>
                </label>
              ))}
            </div>
            {errors.priority && (
              <p className="text-red-500 text-sm mt-1">{errors.priority.message}</p>
            )}
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex-1 px-4 py-2 bg-blue-500 text-white rounded-lg text-sm font-medium hover:bg-blue-600 disabled:opacity-50"
            >
              {isSubmitting ? "Submitting..." : "Submit Request"}
            </button>
          </div>
        </form>
      </div>
    </div>,
    document.body
  );
}
