import pyvista as pv


def test_partitions_collection(tmpdir):
    p = pv.PartitionedDataSet()

    s = pv.Wavelet(extent=[0, 10, 0, 10, 0, 5])

    p1 = pv.ImageData()
    p1.ShallowCopy(s)

    s = pv.Wavelet(extent=[0, 10, 0, 10, 5, 10])

    p2 = pv.ImageData()
    p2.ShallowCopy(s)

    p.SetPartition(0, p1)
    p.SetPartition(1, p2)

    p2 = pv.PartitionedDataSet()
    p2.ShallowCopy(p)

    c = pv.PartitionedDataSetCollection()
    c.SetPartitionedDataSet(0, p)
    c.SetPartitionedDataSet(1, p2)

    fname = "testcompowriread.vtcd"
    c.save(fname)

    o = pv.read(fname)

    assert o.IsA("vtkPartitionedDataSetCollection")
    number_of_datasets = o.GetNumberOfPartitionedDataSets()
    assert number_of_datasets == 2

    for i in range(number_of_datasets):
        p = o.GetPartitionedDataSet(i)
        p2 = c.GetPartitionedDataSet(i)
        assert p.IsA("vtkPartitionedDataSet")
        assert p.GetNumberOfPartitions() == 2
        assert p.GetPartition(0).GetNumberOfCells() == p.GetPartition(0).GetNumberOfCells()
