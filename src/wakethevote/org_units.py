import geopandas as gpd
import numpy as np
import pandas as pd

from . import logger


def get_org_units(blocks: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Given a GeoDataFrame of census blocks for a county with race data, find
    clusters of black house holds

    Args:
        blocks: a GeoDataFrame of census blocks for a county with race data
    """

    # --- Step 1. Select blocks that are majority black and add MECE count data
    logger.debug(" 1. Subsetting blocks that are majority black.")
    blocks = blocks.query("PctBlack >= 50")

    # --- Step 3. Subset majority black blocks with > 50 black HH and save as org1
    #  to be merged with other org units later.
    logger.debug(
        " 3. Keeping majority black blocks with > 50 black households to 'Org1'"
    )
    org1 = blocks.query("BlackHH > 50").reset_index()
    org1.drop(["index", "BLOCKID10", "GEOID10"], axis=1, inplace=True)
    org1["OrgID"] = org1.index + 1
    org1["OrgType"] = "block"

    # --- Step 4. Select the majority black blocks with fewer than 50 black HH for clustering
    logger.debug(" 4. Clustering the remaining blocks...")
    black_hh_lt50 = blocks.query("BlackHH < 50")

    # Step 4a. Cluster adjacent blocks into a single feature and assign a Cluster_id
    logger.debug("  4a. Finding intitial clusters...")

    if len(black_hh_lt50) > 1:
        clusters = gpd.GeoDataFrame(geometry=list(black_hh_lt50.unary_union))
    else:
        clusters = gpd.GeoDataFrame(black_hh_lt50["geometry"]).reset_index()
    clusters["ClusterID"] = clusters.index
    clusters.crs = black_hh_lt50.crs  # Set the coordinate reference system

    # Step 4b. Recalculate population stats for the clusters
    logger.debug("  4b. Computing number of black households in new clusters...")
    # -> Done by first spatially joining the cluster ID to the blocks w/ < 50 Black HH
    black_hh_lt50_2 = gpd.sjoin(black_hh_lt50, clusters, how="left", op="within").drop(
        "index_right", axis=1
    )
    # -> Next we dissolve on the cluster ID computing SUM of the numeric attributes
    #    and updating the percentage fields
    clusters_2 = black_hh_lt50_2.dissolve(by="ClusterID", aggfunc="sum")
    clusters_2["PctBlack"] = clusters_2["P003003"] / clusters_2["P003001"] * 100
    clusters_2["PctBlack18"] = clusters_2["P010004"] / clusters_2["P010001"] * 100

    # Step 4c. Remove block clusters with fewer than 50 BHH; these are impractical
    logger.debug(
        "  4c. Removing clusters still with < 50 black households (impractical)..."
    )
    clusters_2 = clusters_2.query("BlackHH >= 50")

    # Step 4d. Select clusters with fewer than 100 BHH and save as org2, to be merged...
    logger.debug(
        "  4d. Keeping new clusters with fewer than 100 black households: 'Org2'"
    )
    org2 = clusters_2.query("BlackHH <= 100").reset_index()
    org2["OrgID"] = org1["OrgID"].max() + org2.index + 1
    org2["OrgType"] = "block aggregate"

    # Step 4e. For clusters that are too big (> 100 Black HH), cluster incrementally
    #  so that clusters have up to 100 Black HH. These will be saved as org3
    logger.debug("  4e. Reclustering clusters with > 100 HH into smaller aggregates...")
    # -> Get a list of Cluster IDs for block clusters with more than 100 BHH;
    #   we'll cluster individual blocks with these IDs until BHH >= 100
    cluster_ids = clusters_2.query("BlackHH > 100").index.unique()

    # Iterate through each cluster_id
    reclustered = []
    for cluster_id in cluster_ids:
        # Get all the blocks in the selected cluster
        gdfBlksAll = black_hh_lt50_2.query(f"ClusterID == {cluster_id}").reset_index()
        # Assign the X coordinate, used to select the first feature in a sub-cluster
        gdfBlksAll["X"] = gdfBlksAll.geometry.centroid.x
        # Set all blocks to "unclaimed"
        gdfBlksAll["claimed"] = 0
        # Determine how many blocks are unclaimed
        unclaimedCount = gdfBlksAll.query("claimed == 0")["X"].count()
        # Initialize the loop catch variable
        stopLoop = 0
        # Run until all blocks have been "claimed"
        while unclaimedCount > 0:

            # Extract all unclaimed blocks
            gdfBlks = gdfBlksAll[gdfBlksAll.claimed == 0].reset_index()

            # Get the initial block (the western most one); get its BHH and geometry
            gdfBlock = gdfBlks[gdfBlks.X == gdfBlks.X.min()]
            BHH = gdfBlock.BlackHH.sum()
            geom = gdfBlock.geometry.unary_union

            # Expand the geometry until 100 BHH are found
            stopLoop2 = 0  # Loop break check
            while BHH < 100:
                # Select unclaimed blocks that within the area
                gdfNbrs = gdfBlksAll[(gdfBlksAll.touches(geom))]
                gdfBoth = pd.concat((gdfBlock, gdfNbrs), axis="rows", sort=False)
                gdfBlock = gdfBoth.copy(deep=True)
                # Tally the BHHs in the area and update the area shape
                BHH = gdfBoth.BlackHH.sum()
                geom = gdfBoth.geometry.unary_union
                # Catch if run 100 times without getting to 100 BHH
                stopLoop2 += 1
                if stopLoop2 > 100:
                    logger.debug("BHH never reached 100")
                    break

            # Extract features intersecting the geometry to a new dataframe
            gdfSelect = (
                gdfBlksAll[
                    (gdfBlksAll.centroid.within(geom)) & (gdfBlksAll.claimed == 0)
                ]
                .reset_index()
                .dissolve(by="ClusterID", aggfunc="sum")
                .drop(["level_0", "index", "X"], axis=1)
            )

            # Set all features intersecting the shape as "claimed"
            gdfBlksAll.loc[gdfBlksAll.geometry.centroid.within(geom), "claimed"] = 1
            unclaimedCount = gdfBlksAll.query("claimed == 0")["X"].count()

            # Add the dataframe to the list of datarames
            reclustered.append(gdfSelect[gdfSelect["BlackHH"] >= 50])

            # Stop the loop if run for over 100 iterations
            stopLoop += 1
            if stopLoop > 100:
                break

    org_units_list = [org1, org2]

    # -> Concat these to a new geodataframe, update pct fields, and add Org ID and types
    if reclustered:
        logger.debug("    ...completing creating on new clusters: 'Org3'")
        org3 = pd.concat(reclustered, sort=False)
        org3["PctBlack"] = org3["P003003"] / org3["P003001"] * 100
        org3["PctBlack18"] = org3["P010004"] / org3["P010001"] * 100
        org3["OrgID"] = org2["OrgID"].max() + org3.index + 1
        org3["OrgType"] = "block aggregate"
        org3.drop(["claimed"], axis=1, inplace=True)

        org_units_list.append(org3)

    # --- Step 5. Merge all three keepers
    logger.debug(" 5. Combining Org1, Org2, Org3 into a single feature class")
    all_org_units = pd.concat(org_units_list, axis=0, sort=True)

    # --- Step 6. Assign random IDs
    logger.debug(" 6. Assigning random IDs for org units")
    # 1. Compute Random Org IDs
    num_rows = all_org_units.shape[0]

    # Not enough BHH
    if not num_rows:
        return

    all_org_units["Rando"] = np.random.randint(num_rows, size=(num_rows, 1))
    all_org_units.sort_values(by="Rando", axis=0, inplace=True)
    all_org_units.reset_index(inplace=True)
    all_org_units["RandomID"] = all_org_units.index + 1
    all_org_units.drop(["index", "ClusterID", "Rando"], axis=1, inplace=True)

    # --- Step 7. Compute org unit area, in square miles
    logger.debug(" 7. Computing org unit areas (in sq miles)")

    # Project data to State Plane (feet)
    state_plane = all_org_units.to_crs({"init": "epsg:2264"})
    # Compute area, in square miles
    state_plane["area"] = state_plane.geometry.area
    all_org_units["sq_miles"] = state_plane["area"] / 27_878_400  # ft to sq mi

    # --- Step 10. Tidy up and export the org unit feature class
    logger.debug(" 10. Tiding and exporting org unit features...")
    # Rename columns:
    all_org_units.rename(
        columns={
            "precinct_abbrv": "Precinct",
            "P003001": "Total_census_population",
            "P003003": "Total_census_Black_population",
            "PctBlack": "Pct_Black_census",
            "Total": "Total_Black_registered_population",
            "sq_miles": "square_miles",
            "res_city_desc": "city",
        },
        inplace=True,
    )

    # Reorder and subset existing columns
    all_org_units_out = all_org_units.loc[
        :,
        [
            "RandomID",
            "OrgType",
            "Precinct",
            "BlackHH",
            "Total_census_population",
            "Total_census_Black_population",
            "Pct_Black_census",
            "Total_Black_registered_population",
            "square_miles",
            "MECE1",
            "MECE2",
            "MECE3",
            "MECE4",
            "MECE5",
            "city",
            "geometry",
        ],
    ]

    # Append new blank columns
    for new_col in (
        "support_volunteer_name",
        "support_vol_phone",
        "support_vol_email",
        "block_team_member",
        "block_team-phone",
        "block_team_email",
        "Notes",
    ):
        all_org_units_out[new_col] = ""

    return all_org_units
