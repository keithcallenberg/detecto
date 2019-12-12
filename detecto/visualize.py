import cv2
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import torch

from detecto.utils import reverse_normalize, normalize_transform
from torchvision import transforms


# Runs the model predictions on the given video file and produces an output
# video with real-time boxes and labels around detected objects
def detect_video(model, input_file, output_file, scale_down_factor=5, fps=30.0):
    # Read in the video
    video = cv2.VideoCapture(input_file)

    # Video frame dimensions
    frame_width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # The VideoWriter with which we'll write our video with the boxes and labels
    # Parameters: filename, fourcc, fps, frame_size
    out = cv2.VideoWriter(output_file, cv2.VideoWriter_fourcc(*'DIVX'), fps, (frame_width, frame_height))

    # Transform to apply on individual frames of the video
    transform_frame = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize(int(frame_height / scale_down_factor)),
        transforms.ToTensor(),
        normalize_transform(),
    ])

    # TODO make sure this actually works
    # Loop through every frame of the video
    while True:
        ret, frame = video.read()
        # Stop the loop when we're done with the video
        if not ret:
            break

        # The transformed frame is what we'll feed into our model
        transformed_frame = transform_frame(frame)

        # Get our model predictions
        predictions = model.predict_top(transformed_frame)

        # Add the top prediction of each class to the frame
        for label, box, score in predictions:
            # Since the predictions are for scaled down frames, we need to increase the box dimensions
            box *= scale_down_factor

            # Create the box around each object detected
            # Parameters: frame, (start_x, start_y), (end_x, end_y), (r, g, b), thickness
            cv2.rectangle(frame, (box[0], box[1]), (box[2], box[3]), (255, 0, 0), 2)

            # Write the label and score for the boxes
            # Parameters: frame, text, (start_x, start_y), font, font scale, (r, g, b), thickness
            cv2.putText(frame, '{}: {}'.format(label, round(score.item(), 2)), (box[0], box[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

        # Write this frame to our video file
        out.write(frame)

        # If the 'q' key is pressed, break from the loop
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break

    # When finished, release the video capture and writer objects
    video.release()
    out.release()

    # Closes all the frames
    cv2.destroyAllWindows()


def plot_prediction_grid(model, images, dim):
    # TODO pass in a single number for dim
    if dim[0] * dim[1] != len(images):
        print('Grid dimensions do not match size of list of images')

    # TODO figsize adjust
    fig, axes = plt.subplots(dim[0], dim[1], figsize=(dim[0] * 5, dim[1] * 4))

    index = 0
    for i in range(dim[0]):
        for j in range(dim[1]):
            # TODO make sure this actually works
            # Get the predictions and plot the box with the highest score
            preds = model.predict_top(images[index])
            index += 1

            image = transforms.ToPILImage()(reverse_normalize(images[index]))
            axes[i, j].imshow(image)

            for _, box, _ in preds:
                width, height = box[2] - box[0], box[3] - box[1]
                initial_pos = (box[0], box[1])
                rect = patches.Rectangle(initial_pos, width, height, linewidth=1,
                                         edgecolor='r', facecolor='none')
                axes[i, j].add_patch(rect)
            axes[i, j].set_title('Highest prediction: {} (score: {})'
                                 .format(preds[0][0], round(preds[0][2].item(), 2)))

    plt.show()


# Show the image along with the specified boxes around the labeled item
def show_labeled_image(image, boxes):
    fig, ax = plt.subplots(1)
    # If the image is already a tensor, convert it back to a PILImage
    if isinstance(image, torch.Tensor):
        image = transforms.ToPILImage()(image)
    ax.imshow(image)

    # Show a single box or multiple if provided
    if boxes.ndim == 1:
        boxes = [boxes]
    for box in boxes:
        width, height = box[2] - box[0], box[3] - box[1]
        initial_pos = (box[0], box[1])
        rect = patches.Rectangle(initial_pos,  width, height, linewidth=1,
                                 edgecolor='r', facecolor='none')

        ax.add_patch(rect)
    plt.show()